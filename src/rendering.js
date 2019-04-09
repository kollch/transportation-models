'use strict'

const { vec2, vec4, mat4 } = glMatrix;

const secure = false;

const url = 'localhost';
const port = 8888;

const enableBuild = () => {
  const infrBtn = document.getElementById("infrInput");
  const vehicleBtn = document.getElementById("vehicleInput");
  const buildBtn = document.getElementById("build");
  // If not ready to build
  if (infrBtn.files.length !== 1 || vehicleBtn.files.length !== 1) {
    buildBtn.disabled = true;
    return;
  }
  buildBtn.disabled = false;
};

const build = () => {
  let infrastructure = null;
  const infrReader = new FileReader();
  infrReader.onload = e => {
    let infrData;
    try {
      infrData = JSON.parse(e.target.result);
    } catch(err) {
      alert("Infrastructure file is not valid JSON!");
      throw err;
    }
    infrastructure = infrData;
    const vehicleReader = new FileReader();
    vehicleReader.onload = e => {
      let vehicleData;
      try {
        vehicleData = JSON.parse(e.target.result);
      } catch(err) {
        alert("Vehicles file is not valid JSON!");
        throw err;
      }
      // Establish a websocket connection
      let socketLoc = '://' + url + ':' + port.toString();
      if (secure) {
        socketLoc = 'wss' + socketLoc;
      } else {
        socketLoc = 'ws' + socketLoc;
      }
      const socket = new WebSocket(socketLoc);
      socket.onerror = e => {
        alert("Can't establish a connection with the server! Verify the backend is running and refresh the page.");
      };
      socket.onopen = e => {
        // Ready to start sending
        /* Pass data to and from backend */
        const frames = [];

        // Hide the build button
        document.getElementById("build").style.display = "none";

        socket.onmessage = e => {
          const frame = JSON.parse(e.data);
          // If all simulation frames have been received
          if (frame === null && infrastructure !== null) {
            main(frames, infrastructure);
          } else {
            frames.push(frame);
          }
        };
        // Send parameters to the server
        socket.send(JSON.stringify(infrData));
        socket.send(JSON.stringify(vehicleData));
      };
    }
    const vehicleFile = document.getElementById("vehicleInput").files[0];
    vehicleReader.readAsText(vehicleFile);
  };
  const infrFile = document.getElementById("infrInput").files[0];
  infrReader.readAsText(infrFile);
};

const getDimensions = infrastructure => {
  let viewDims = {
    "x": 0,
    "y": 0
  };
  for (let i in infrastructure.roads) {
    const roadCoords = infrastructure.roads[i].ends;
    for (let j = 0; j < 2; j++) {
      if (isNaN(roadCoords[j])) {
        const updateDim = a => {
          if (roadCoords[j][a] > viewDims[a]) {
            viewDims[a] = roadCoords[j][a];
          }
        };
        updateDim("x");
        updateDim("y");
      }
    }
  }
  return viewDims;
};

const playPause = pause => {
  paused = pause;
}

const main = (frames, infrastructure) => {
  const canvas = document.querySelector("#glCanvas");
  const viewDims = getDimensions(infrastructure);
  const aspect = viewDims.x / viewDims.y;
  canvas.width = canvas.clientWidth;
  canvas.height = canvas.clientHeight;
  // Initialize the GL context
  const gl = canvas.getContext("webgl");

  // Only continue if WebGL is available and working
  if (gl === null) {
    alert("Unable to initialize WebGL. Your browser or machine may not support it.");
    return;
  }

  const vsSource = `
    attribute vec4 aVertexPosition;

    uniform mat4 uModelViewMatrix;
    uniform mat4 uProjectionMatrix;

    void main() {
      gl_Position = uProjectionMatrix * uModelViewMatrix * aVertexPosition;
    }
  `;

  const fsSource = `
    void main() {
      gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);
    }
  `;

  // Initialize a shader program - lighting for the vertices and so forth
  const shaderProgram = initShaderProgram(gl, vsSource, fsSource);

  const programInfo = {
    program: shaderProgram,
    attribLocations: {
      vertexPosition: gl.getAttribLocation(shaderProgram, 'aVertexPosition'),
    },
    uniformLocations: {
      projectionMatrix: gl.getUniformLocation(shaderProgram, 'uProjectionMatrix'),
      modelViewMatrix: gl.getUniformLocation(shaderProgram, 'uModelViewMatrix'),
    },
  };

  // Set parameters for clearing
  gl.clearColor(1.0, 1.0, 1.0, 1.0); // Clear to white, fully opaque
  gl.clearDepth(1.0);                // Clear everything
  gl.enable(gl.DEPTH_TEST);          // Enable depth testing
  gl.depthFunc(gl.LEQUAL);           // Near things obscure far things

  // Tell WebGL to use our program when drawing
  gl.useProgram(programInfo.program);

  // Set the viewport size
  if (aspect > 1) {
    gl.viewport(0, 0, canvas.width, canvas.width / aspect);
  } else {
    gl.viewport(0, 0, canvas.height * aspect, canvas.height);
  }

  const infrBuf = gl.createBuffer();
  const rectBuf = gl.createBuffer();

  let zoom = 1;
  let screenLoc = {
    "x": 0,
    "y": 0
  };
  setupCamera(gl, programInfo, viewDims, zoom, screenLoc);
  window.addEventListener("resize", () => {
    canvas.width = canvas.clientWidth;
    canvas.height = canvas.clientHeight;
    if (aspect > 1) {
      gl.viewport(0, 0, canvas.width, canvas.width / aspect);
    } else {
      gl.viewport(0, 0, canvas.height * aspect, canvas.height);
    }
  });
  window.addEventListener("wheel", e => {
    const cursorFrac = {
      "x": e.offsetX / canvas.width,
      "y": 1 - e.offsetY / canvas.height
    };
    const cursorLoc = {
      "x": screenLoc.x + cursorFrac.x * viewDims.x / zoom,
      "y": screenLoc.y + cursorFrac.y * viewDims.y / zoom
    };
    zoom -= e.deltaY * 0.1;
    if (zoom < 1) {
      zoom = 1;
    }
    const setScreenLoc = a => {
      const newViewportSize = viewDims[a] / zoom;
      if (screenLoc[a] < 0) {
        return 0;
      } else if (screenLoc[a] + newViewportSize > viewDims[a]) {
        return viewDims[a] - newViewportSize;
      }
      return cursorLoc[a] - cursorFrac[a] * newViewportSize;
    };
    screenLoc.x = setScreenLoc("x");
    screenLoc.y = setScreenLoc("y");

    setupCamera(gl, programInfo, viewDims, zoom, screenLoc);
  });

  // Set up the infrastructure buffer
  useBuffer(gl, programInfo, infrBuf);
  let infrNum = setupInfr(gl, infrastructure);

  const playBtn = document.getElementById("play");
  const pauseBtn = document.getElementById("pause");
  const replayBtn = document.getElementById("replay");

  var paused = false;
  var time = 0;
  var numFrames = frames.length;
  // Duplicate last frame so that interpolation always has two frames to use
  frames.push(frames[frames.length - 1]);
  var then = performance.now();
  // Draw the scene repeatedly
  const render = now => {
    // Ignore if then > now because of async
    if (now > then) {
      time += now - then;
    }
    const frame = time / 100 + 1;
    const currFrame = Math.floor(frame);
    then = now;

    // Clear the canvas before drawing
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

    drawInfr(gl, programInfo, infrBuf, infrNum);
    drawVehicles(gl, now, frame % 1, programInfo, rectBuf, frames, currFrame);
    if (currFrame < numFrames && !paused) {
      requestAnimationFrame(render);
    }
    if (currFrame >= numFrames) {
      playBtn.style.display = "none";
      pauseBtn.style.display = "none";
    }
  };

  requestAnimationFrame(render);
  playBtn.onclick = () => {
    playBtn.disabled = true;
    pauseBtn.disabled = false;
    if (paused) {
      paused = false;
      then = performance.now();
      requestAnimationFrame(render);
    }
  }
  pauseBtn.onclick = () => {
    playBtn.disabled = false;
    pauseBtn.disabled = true;
    if (!paused) {
      paused = true;
    }
  }
  replayBtn.onclick = () => {
    playBtn.style.display = "initial";
    pauseBtn.style.display = "initial";
    time = 0;
    then = performance.now();
    requestAnimationFrame(render);
  }
  playBtn.disabled = true;
  playBtn.style.display = "initial";
  pauseBtn.style.display = "initial";
  replayBtn.style.display = "initial";
};

const setupCamera = (gl, programInfo, viewDims, zoom, screenLoc) => {
  const projectionMatrix = mat4.create();

  mat4.ortho(projectionMatrix, 0, viewDims.x, 0, viewDims.y, 0, 1);

  // Set drawing position to the "identity" point (bottom left point of the scene)
  const modelViewMatrix = mat4.create();

  mat4.scale(projectionMatrix, projectionMatrix, [zoom, zoom, 1]);
  mat4.translate(projectionMatrix, projectionMatrix, [-screenLoc.x, -screenLoc.y, 0]);

  // Set the shader uniforms
  gl.uniformMatrix4fv(programInfo.uniformLocations.projectionMatrix, false, projectionMatrix);
  gl.uniformMatrix4fv(programInfo.uniformLocations.modelViewMatrix, false, modelViewMatrix);
};

const setupInfr = (gl, infrastructure) => {
  let allPositions = [];
  let intersections = [];
  const roadAngle = road => {
    /* Return the angle of the road with regards to the x axis */
    let loc1 = road.ends[0];
    let loc2 = road.ends[1];
    // Check if element is a number; if so, retrieve loc from intersections
    if (!isNaN(loc1)) {
      loc1 = infrastructure.intersections.find(x => x.id === loc1).loc;
    }
    if (!isNaN(loc2)) {
      loc2 = infrastructure.intersections.find(x => x.id === loc2).loc;
    }
    return Math.abs(Math.atan((loc2.y - loc1.y) / (loc2.x - loc1.x)));
  };
  const addIntersections = () => {
    for (let i in infrastructure.intersections) {
      const intersection = infrastructure.intersections[i];
      let intersectionInfo = {
        "id": intersection.id,
        "roads": []
      };
      // Width, height
      let dims = [0, 0];
      // Up to 4 roads connect to an intersection
      for (let j = 0; j < 4; j++) {
        const roadId = intersection.connects_roads[j];
        const road = infrastructure.roads.find(x => x.id === roadId);
        if (road === undefined) {
          continue;
        }
        // 12 is the width of a lane
        const roadWidth = road.lanes * 12;
        if (j % 2 === 0) {
          dims[0] = Math.max(dims[0], roadWidth / Math.sin(roadAngle(road)));
        } else {
          dims[1] = Math.max(dims[1], roadWidth / Math.cos(roadAngle(road)));
        }
      }
      // Round lane widths up
      const halfWidth = Math.ceil(dims[0] / 2);
      const halfHeight = Math.ceil(dims[1] / 2);
      let points = [
        vec2.fromValues(-halfWidth, halfHeight),
        vec2.fromValues(halfWidth, halfHeight),
        vec2.fromValues(halfWidth, -halfHeight),
        vec2.fromValues(-halfWidth, -halfHeight)
      ];
      if (points.length != 4) {
        throw new Error("Incorrect number of intersection points!");
      }
      const intersectionOrigin = vec2.fromValues(intersection.loc.x, intersection.loc.y);
      // Add the intersection origin to the offsets
      for (let j = 0; j < 4; j++) {
        vec2.add(points[j], points[j], intersectionOrigin);
      }
      // Separate loop because all points must be calculated first
      for (let j = 0; j < 4; j++) {
        const roadId = intersection.connects_roads[j];
        if (roadId === null) {
          continue;
        }
        /* Get vertical or horizontal width of road;
         * negative value specifies the road is horizontal */
        let roadLoc = vec2.create();
        // Figure out if offset is positive or negative
        let sign = 1;
        if (j > 1) {
          sign = -1;
        }
        // Set offset
        let offset;
        if (j % 2 === 0) {
          offset = vec2.fromValues(0, sign * halfHeight);
        } else {
          offset = vec2.fromValues(sign * halfWidth, 0);
        }
        vec2.add(roadLoc, intersectionOrigin, offset);
        intersectionInfo.roads.push({
          "id": roadId,
          "loc": roadLoc
        });
      }
      intersections.push(intersectionInfo);
      allPositions.push(points);
    }
    return allPositions;
  };
  const addRoads = () => {
    let vectorPairs = [];
    for (let i in infrastructure.roads) {
      const road = infrastructure.roads[i];
      const angle = roadAngle(road);
      // 12 is the width of a lane
      const roadWidth = road.lanes * 12;
      let offset;
      // Determine if road is horizontal or vertical
      if (angle > glMatrix.glMatrix.toRadian(45)) {
        offset = vec2.fromValues(roadWidth / Math.sin(angle) / 2, 0);
      } else {
        offset = vec2.fromValues(0, roadWidth / Math.cos(angle) / 2);
      }
      // Add points for the four outer corners of the road
      let points = [];
      for (let j = 0; j < 4; j++) {
        const end = road.ends[j % 2];
        if (isNaN(end)) {
          points[j] = vec2.fromValues(end.x, end.y);
        } else {
          points[j] = vec2.clone(intersections.find(x => x.id === end).roads.find(x => x.id === road.id).loc);
        }
        if (j < 2) {
          vec2.add(points[j], points[j], offset);
        } else {
          vec2.sub(points[j], points[j], offset);
        }
        if (j % 2 === 1) {
          const pointPair = [
            points[j - 1],
            points[j]
          ];
          vectorPairs.push(pointPair);
        }
      }
      // Add points for the lanes of the road
      for (let j = 1; j < road.lanes; j++) {
        let pointPair = [];
        // One point per end of the road
        for (let k = 0; k < 2; k++) {
          const base = points[k + 2];
          let lanePoint = vec2.create();
          vec2.scaleAndAdd(lanePoint, base, offset, 2 * j / road.lanes);
          pointPair.push(lanePoint);
        }
        vectorPairs.push(pointPair);
      }
    }
    return vectorPairs;
  };
  const intersectionCoords = addIntersections();
  const roadCoords = addRoads();
  initBuffer(gl, intersectionCoords.length * 4 + roadCoords.length * 2);
  storeToBuffer(gl, 4, intersectionCoords, 0);
  storeToBuffer(gl, 2, roadCoords, intersectionCoords.length * 32);
  return {
    "rect": intersectionCoords.length,
    "line": roadCoords.length
  };
};

const drawInfr = (gl, programInfo, buffer, infrNum) => {
  useBuffer(gl, programInfo, buffer);
  /* Don't call drawPoints() because the checks don't work */
  // Draw rectangles
  for (let i = 0; i < infrNum.rect; i++) {
    gl.drawArrays(gl.LINE_LOOP, i * 4, 4);
  }
  const offset = infrNum.rect * 4;
  // Draw lines
  for (let i = 0; i < infrNum.line; i++) {
    gl.drawArrays(gl.LINES, offset + i * 2, 2);
  }
};

const drawVehicles = (gl, now, dTime, programInfo, buffer, frames, frame) => {
  useBuffer(gl, programInfo, buffer);
  const vehicles = vehiclePos(frames, frame, dTime);
  initBuffer(gl, vehicles.length * 4);
  storeToBuffer(gl, 4, vehicles, 0);
  drawPoints(gl, 4, gl.TRIANGLE_STRIP);
};

const vehiclePos = (frames, frame, dTime) => {
  let allPositions = [];
  for (let i in frames[frame - 1].vehicles) {
    // Vehicle in last frame and current frame
    const vehicle1 = frames[frame - 1].vehicles[i];
    const vehicle2 = frames[frame].vehicles.find(x => x.id === vehicle1.id);
    if (vehicle2 === undefined) {
      continue;
    }
    const vehicle1Loc = vec2.fromValues(vehicle1.loc.x, vehicle1.loc.y);
    const vehicle2Loc = vec2.fromValues(vehicle2.loc.x, vehicle2.loc.y);
    const vehicle1Dir = vehicle1.direction;
    const vehicle2Dir = vehicle2.direction;
    let vehicleLoc = vec2.create();
    vec2.lerp(vehicleLoc, vehicle1Loc, vehicle2Loc, dTime);
    const lerp = (a, b, diff) => {
      if (a >= 180) {
        if (b < a - 180) {
          b += 360;
        }
      } else if (b > a + 180) {
        a += 360;
      }
      return a * (1 - diff) + b * diff;
    };
    const vehicleDir = glMatrix.glMatrix.toRadian(lerp(vehicle1Dir, vehicle2Dir, dTime));
    // Positions for the object
    let positions = [
      vec2.fromValues(5, 4),
      vec2.fromValues(-10, 4),
      vec2.fromValues(10, -4),
      vec2.fromValues(-10, -4)
    ];
    for (let j in positions) {
      vec2.add(positions[j], positions[j], vehicleLoc);
      vec2.rotate(positions[j], positions[j], vehicleLoc, vehicleDir);
    }
    allPositions.push(positions);
  }
  return allPositions;
};

const initBuffer = (gl, length) => {
  // 8 because there are 2 values for every point, each value of size 4 bytes
  gl.bufferData(gl.ARRAY_BUFFER, length * 8, gl.STATIC_DRAW);
};

const storeToBuffer = (gl, type, allPositions, offset) => {
  for (let i in allPositions) {
    const positions = allPositions[i];
    let coords = new Float32Array(2 * type);
    // 2 because there are 2 values for every point (2D)
    positions.forEach((item, j) => {
      coords.set(item, j * 2);
    });
    // Store positions into the buffer
    gl.bufferSubData(gl.ARRAY_BUFFER, offset + i * 8 * type, coords);
  }
};

const useBuffer = (gl, programInfo, buffer) => {
  // Set 'buffer' as the one to apply buffer operations to
  gl.bindBuffer(gl.ARRAY_BUFFER, buffer);

  gl.vertexAttribPointer(programInfo.attribLocations.vertexPosition, 2, gl.FLOAT, false, 0, 0);
  gl.enableVertexAttribArray(programInfo.attribLocations.vertexPosition);
};

const drawPoints = (gl, vertexCount, type) => {
  const pointSize = 8 * vertexCount;
  // Get the size of the buffer and check that it's valid
  const bufSize = gl.getBufferParameter(gl.ARRAY_BUFFER, gl.BUFFER_SIZE);
  if (!Number.isInteger(bufSize / pointSize)) {
    console.warn("Buffer is not a valid size!");
  }
  // Draw vertices on the screen
  for (let i = 0; i < bufSize / pointSize; i++) {
    gl.drawArrays(type, i * vertexCount, vertexCount);
  }
};

const initShaderProgram = (gl, vsSource, fsSource) => {
  const vertexShader = loadShader(gl, gl.VERTEX_SHADER, vsSource);
  const fragmentShader = loadShader(gl, gl.FRAGMENT_SHADER, fsSource);

  // Create the shader program
  const newShaderProgram = gl.createProgram();
  gl.attachShader(newShaderProgram, vertexShader);
  gl.attachShader(newShaderProgram, fragmentShader);
  gl.linkProgram(newShaderProgram);

  // If creating the shader program failed then alert
  if (!gl.getProgramParameter(newShaderProgram, gl.LINK_STATUS)) {
    alert('Unable to initialize the shader program: ' + gl.getProgramInfoLog(newShaderProgram));
    return null;
  }

  return newShaderProgram;
};

// Creates a shader of the given type, uploads the source, and compiles it.
const loadShader = (gl, type, source) => {
  const shader = gl.createShader(type);

  gl.shaderSource(shader, source);
  gl.compileShader(shader);

  // See if it compiled successfully
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    alert('An error occurred compiling the shaders: ' + gl.getShaderInfoLog(shader));
    gl.deleteShader(shader);
    return null;
  }

  return shader;
};
