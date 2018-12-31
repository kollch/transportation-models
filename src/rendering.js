const { vec2, vec4, mat4 } = glMatrix;

var viewWidth = 1600;
var viewHeight = 1600;

var infrastructure;
var frames;
document.addEventListener("DOMContentLoaded", () => {
  // Retrieve data from json files for now until we can pull from the backend
  let requestLoc = './data.json';
  let request = new XMLHttpRequest();
  request.open('GET', requestLoc);
  request.responseType = 'json';
  request.send();
  request.onload = () => {
    infrastructure = request.response;
    requestLoc = './testframes.json';
    request = new XMLHttpRequest();
    request.open('GET', requestLoc);
    request.responseType = 'json';
    request.send();
    request.onload = () => {
      frames = request.response;
      main();
    }
  }

  function main() {
    const canvas = document.querySelector("#glCanvas");
    //canvas.width = viewWidth;
    //canvas.height = viewHeight;
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

    const infrBuf = gl.createBuffer();
    const rectBuf = gl.createBuffer();

    const zoom = 1;
    setupCamera(gl, programInfo, zoom);

    // Set up the infrastructure buffer
    useBuffer(gl, programInfo, infrBuf);
    let infrNum = setupInfr(gl);

    var time = 0;
    var numFrames = frames.length;
    var then = performance.now();
    // Draw the scene repeatedly
    function render(now) {
      // Ignore if then > now because of async
      if (now > then) {
        time += now - then;
      }
      const frame = time / 1000 + 1;
      const currFrame = Math.floor(frame);
      then = now;

      if (currFrame >= numFrames) {
        return;
      }

      // Clear the canvas before drawing
      gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

      drawInfr(gl, programInfo, infrBuf, infrNum);
      drawVehicles(gl, now, frame % 1, programInfo, rectBuf, currFrame);
      requestAnimationFrame(render);
    }

    requestAnimationFrame(render);
  }

  function setupCamera(gl, programInfo, zoom) {
    const projectionMatrix = mat4.create();

    // Not currently used, but useful to know the aspect ratio
    //const aspect = gl.canvas.clientWidth / gl.canvas.clientHeight;

    mat4.ortho(projectionMatrix, 0, viewWidth, 0, viewHeight, 0, 1);

    // Set drawing position to the "identity" point (bottom left point of the scene)
    const modelViewMatrix = mat4.create();

    mat4.scale(projectionMatrix, projectionMatrix, [zoom, zoom, 1]);
    mat4.translate(projectionMatrix, projectionMatrix, [0, 0, 0]);

    // Set the shader uniforms
    gl.uniformMatrix4fv(programInfo.uniformLocations.projectionMatrix, false, projectionMatrix);
    gl.uniformMatrix4fv(programInfo.uniformLocations.modelViewMatrix, false, modelViewMatrix);
  }

  function setupInfr(gl) {
    let allPositions = [];
    let intersections = [];
    function roadAngle(road) {
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
    }
    function addIntersections() {
      for (i in infrastructure.intersections) {
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
          console.log("ERROR: incorrect number of intersection points!");
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
    }
    function addRoads() {
      let vectorPairs = [];
      for (i in infrastructure.roads) {
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
    }
    const intersectionCoords = addIntersections();
    const roadCoords = addRoads();
    initBuffer(gl, intersectionCoords.length * 4 + roadCoords.length * 2);
    storeToBuffer(gl, 4, intersectionCoords, 0);
    storeToBuffer(gl, 2, roadCoords, intersectionCoords.length * 32);
    return {
      "rect": intersectionCoords.length,
      "line": roadCoords.length
    };
  }

  function drawInfr(gl, programInfo, buffer, infrNum) {
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
  }

  function drawVehicles(gl, now, dTime, programInfo, buffer, frame) {
    useBuffer(gl, programInfo, buffer);
    const vehicles = vehiclePos(frame, dTime);
    initBuffer(gl, vehicles.length * 4);
    storeToBuffer(gl, 4, vehicles, 0);
    drawPoints(gl, 4, gl.TRIANGLE_STRIP);
  }

  function vehiclePos(frame, dTime) {
    let allPositions = [];
    for (i in frames[frame - 1].vehicles) {
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
      function lerp(a, b, diff) {
        if (a >= 180) {
          if (b < a - 180) {
            b += 360;
          }
        } else if (b > a + 180) {
          a += 360;
        }
        return a * (1 - diff) + b * diff;
      }
      const vehicleDir = glMatrix.glMatrix.toRadian(lerp(vehicle1Dir, vehicle2Dir, dTime));
      // Positions for the object
      let positions = [
        vec2.fromValues(5, 4),
        vec2.fromValues(-10, 4),
        vec2.fromValues(10, -4),
        vec2.fromValues(-10, -4)
      ];
      for (j in positions) {
        vec2.add(positions[j], positions[j], vehicleLoc);
        vec2.rotate(positions[j], positions[j], vehicleLoc, vehicleDir);
      }
      allPositions.push(positions);
    }
    return allPositions;
  }

  function initBuffer(gl, length) {
    // 8 because there are 2 values for every point, each value of size 4 bytes
    gl.bufferData(gl.ARRAY_BUFFER, length * 8, gl.STATIC_DRAW);
  }

  function storeToBuffer(gl, type, allPositions, offset) {
    for (i in allPositions) {
      const positions = allPositions[i];
      let coords = new Float32Array(2 * type);
      // 2 because there are 2 values for every point (2D)
      positions.forEach((item, j) => {
        coords.set(item, j * 2);
      });
      // Store positions into the buffer
      gl.bufferSubData(gl.ARRAY_BUFFER, offset + i * 8 * type, coords);
    }
  }

  function useBuffer(gl, programInfo, buffer) {
    // Set 'buffer' as the one to apply buffer operations to
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);

    gl.vertexAttribPointer(programInfo.attribLocations.vertexPosition, 2, gl.FLOAT, false, 0, 0);
    gl.enableVertexAttribArray(programInfo.attribLocations.vertexPosition);
  }

  function drawPoints(gl, vertexCount, type) {
    const pointSize = 8 * vertexCount;
    // Get the size of the buffer and check that it's valid
    const bufSize = gl.getBufferParameter(gl.ARRAY_BUFFER, gl.BUFFER_SIZE);
    if (!Number.isInteger(bufSize / pointSize)) {
      console.log("WARNING: Buffer is not a valid size!");
    }
    // Draw vertices on the screen
    for (let i = 0; i < bufSize / pointSize; i++) {
      gl.drawArrays(type, i * vertexCount, vertexCount);
    }
  }

  // Initialize a shader program so WebGL knows how to draw our data
  function initShaderProgram(gl, vsSource, fsSource) {
    const vertexShader = loadShader(gl, gl.VERTEX_SHADER, vsSource);
    const fragmentShader = loadShader(gl, gl.FRAGMENT_SHADER, fsSource);

    // Create the shader program
    const shaderProgram = gl.createProgram();
    gl.attachShader(shaderProgram, vertexShader);
    gl.attachShader(shaderProgram, fragmentShader);
    gl.linkProgram(shaderProgram);

    // If creating the shader program failed then alert
    if (!gl.getProgramParameter(shaderProgram, gl.LINK_STATUS)) {
      alert('Unable to initialize the shader program: ' + gl.getProgramInfoLog(shaderProgram));
      return null;
    }

    return shaderProgram;
  }

  // Creates a shader of the given type, uploads the source, and compiles it.
  function loadShader(gl, type, source) {
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
  }
});
