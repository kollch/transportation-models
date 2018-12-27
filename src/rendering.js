const { vec2, vec4, mat4 } = glMatrix;

var viewWidth = 1600;
var viewHeight = 1600;

var infrastructure = {
  "intersections": [
    {
      "id": 1,
      "connects_roads": [
        1,
        2,
        3
      ],
      "loc": {
        "x": 500,
        "y": 500
      }
    },
    {
      "id": 2,
      "connects_roads": [
        2,
        4,
        5,
        6
      ],
      "loc": {
        "x": 400,
        "y": 1000
      }
    },
    {
      "id": 3,
      "connects_roads": [
        6,
        7,
        8,
        9
      ],
      "loc": {
        "x": 1100,
        "y": 1000
      }
    },
    {
      "id": 4,
      "connects_roads": [
        3,
        9,
        10,
        11
      ],
      "loc": {
        "x": 900,
        "y": 600
      }
    }
  ],
  "roads": [
    {
      "id": 1,
      "ends": [
        1,
        {
          "x": 0,
          "y": 500
        }
      ],
      "two-way": true,
      "lanes": 1
    },
    {
      "id": 2,
      "ends": [
        1,
        2
      ],
      "two-way": true,
      "lanes": 1
    },
    {
      "id": 3,
      "ends": [
        1,
        4
      ],
      "two-way": true,
      "lanes": 1
    },
    {
      "id": 4,
      "ends": [
        {
          "x": 0,
          "y": 1000
        },
        2
      ],
      "two-way": true,
      "lanes": 2
    },
    {
      "id": 5,
      "ends": [
        2,
        {
          "x": 400,
          "y": 1500
        }
      ],
      "two-way": true,
      "lanes": 1
    },
    {
      "id": 6,
      "ends": [
        2,
        3
      ],
      "two-way": true,
      "lanes": 2
    },
    {
      "id": 7,
      "ends": [
        3,
        {
          "x": 1100,
          "y": 1500
        }
      ],
      "two-way": true,
      "lanes": 1
    },
    {
      "id": 8,
      "ends": [
        3,
        {
          "x": 1600,
          "y": 1000
        }
      ],
      "two-way": true,
      "lanes": 2
    },
    {
      "id": 9,
      "ends": [
        4,
        3
      ],
      "two-way": false,
      "lanes": 2
    },
    {
      "id": 10,
      "ends": [
        4,
        {
          "x": 1600,
          "y": 600
        }
      ],
      "two-way": true,
      "lanes": 1
    },
    {
      "id": 11,
      "ends": [
        {
          "x": 900,
          "y": 0
        },
        4
      ],
      "two-way": false,
      "lanes": 1
    },
  ]
}

var jsonFrame = [
  {
    "frameid": 1,
    "vehicles": [
      {
        "id": 1,
        "loc": {
          "x": 400,
          "y": 400
        },
        "direction": 0
      },
      {
        "id": 2,
        "loc": {
          "x": 200,
          "y": 400
        },
        "direction": 90
      },
      {
        "id": 3,
        "loc": {
          "x": 400,
          "y": 200
        },
        "direction": 330
      },
      {
        "id": 4,
        "loc": {
          "x": 200,
          "y": 200
        },
        "direction": 45
      }
    ]
  },
  {
    "frameid": 2,
    "vehicles": [
      {
        "id": 1,
        "loc": {
          "x": 300,
          "y": 300
        },
        "direction": 90
      },
      {
        "id": 2,
        "loc": {
          "x": 100,
          "y": 300
        },
        "direction": 45
      },
      {
        "id": 3,
        "loc": {
          "x": 300,
          "y": 100
        },
        "direction": 0
      },
      {
        "id": 4,
        "loc": {
          "x": 100,
          "y": 100
        },
        "direction": 330
      }
    ]
  }
];

document.addEventListener("DOMContentLoaded", () => {
  main();

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

    const lineBuf = gl.createBuffer();
    const rectBuf = gl.createBuffer();

    const zoom = 4;
    setupCamera(gl, programInfo, zoom);

    // Set up the buffer
    //useBuffer(gl, programInfo, rectBuf);

    var time = 0;
    var numFrames = jsonFrame.length;
    var then = performance.now();
    // Draw the scene repeatedly
    function render(now) {
      time += now - then;
      const frame = time / 1000 + 1;
      const currFrame = Math.floor(frame);
      then = now;

      if (currFrame >= numFrames) {
        return;
      }

      // Clear the canvas before drawing
      gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

      drawInfrastructure(gl, now, time % 1, programInfo, lineBuf);
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

  function drawVehicles(gl, now, dTime, programInfo, buffer, frame) {
    useBuffer(gl, programInfo, buffer);
    //console.log(frame + dTime / 1000);
    storeToBuffer(gl, 4, vehiclePos(frame, dTime));
    drawPoints(gl, now, dTime, 4, gl.TRIANGLE_STRIP);
  }

  function drawInfrastructure(gl, now, dTime, programInfo, buffer) {
    useBuffer(gl, programInfo, buffer);
    let points = [[
      vec2.fromValues(300, 300),
      vec2.fromValues(320, 320)
    ]];
    storeToBuffer(gl, 2, points);
    drawPoints(gl, now, dTime, 2, gl.LINE_STRIP);
  }

  function vehiclePos(frame, dTime) {
    let allPositions = [];
    for (i in jsonFrame[frame - 1]["vehicles"]) {
      const vehicle1 = jsonFrame[frame - 1]["vehicles"][i];
      const vehicle2 = jsonFrame[frame]["vehicles"].find(x => x.id === vehicle1.id);
      if (vehicle2 === undefined) {
        continue;
      }
      const vehicle1Loc = vec2.fromValues(vehicle1["loc"]["x"], vehicle1["loc"]["y"]);
      const vehicle2Loc = vec2.fromValues(vehicle2["loc"]["x"], vehicle2["loc"]["y"]);
      const vehicle1Dir = vehicle1["direction"];
      const vehicle2Dir = vehicle2["direction"];
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

  function storeToBuffer(gl, type, allPositions) {
    // 8 because there are 2 values for every point, each value of size 4 bytes
    gl.bufferData(gl.ARRAY_BUFFER, allPositions.length * 8 * type, gl.STATIC_DRAW);

    for (i in allPositions) {
      const positions = allPositions[i];
      let coords = new Float32Array(2 * type);
      // 2 because there are 2 values for every point (2D)
      positions.forEach((item, j) => {
        coords.set(item, j * 2);
      });
      // Store positions into the buffer
      gl.bufferSubData(gl.ARRAY_BUFFER, i * 8 * type, coords);
    }
  }

  function useBuffer(gl, programInfo, buffer) {
    // Set 'buffer' as the one to apply buffer operations to
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);

    gl.vertexAttribPointer(programInfo.attribLocations.vertexPosition, 2, gl.FLOAT, false, 0, 0);
    gl.enableVertexAttribArray(programInfo.attribLocations.vertexPosition);
  }

  function drawPoints(gl, currTime, dTime, vertexCount, type) {
    const pointSize = 8 * vertexCount;
    // Get the size of the buffer and check that it's valid
    const bufSize = gl.getBufferParameter(gl.ARRAY_BUFFER, gl.BUFFER_SIZE);
    if (!Number.isInteger(bufSize / pointSize)) {
      console.log("WARNING: Buffer is not a valid size!");
    }
    // Draw vertices on the screen
    for (let i = 0; i < bufSize / pointSize; i++) {
      gl.drawArrays(type, i * 4, vertexCount);
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
