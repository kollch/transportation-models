const { vec2, vec4, mat4 } = glMatrix;

var jsonFrame = {
  "frameid": 1,
  "vehicles": [
    {
      "id": 1,
      "loc": {
        "x": 0.5,
        "y": 0.5
      },
      "direction": 0
    },
    {
      "id": 2,
      "loc": {
        "x": -0.5,
        "y": 0.5
      },
      "direction": 90
    },
    {
      "id": 3,
      "loc": {
        "x": 0.5,
        "y": -0.5
      },
      "direction": 330
    },
    {
      "id": 4,
      "loc": {
        "x": -0.5,
        "y": -0.5
      },
      "direction": 45
    }
  ]
}

document.addEventListener("DOMContentLoaded", () => {
  main();

  function main() {
    const canvas = document.querySelector("#glCanvas");
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

    // Build all of the objects to be drawn
    const buffers = initBuffers(gl);

    var then = 0;

    // Draw the scene repeatedly
    function render(now) {
      const dTime = now - then;
      then = now;

      drawScene(gl, programInfo, buffers, now, dTime);
      requestAnimationFrame(render);
    }

    requestAnimationFrame(render);
  }

  function storeToBuffer(gl, buffer) {
    // 32 because there are 4 points with 2 values each, each value of size 4 bytes
    gl.bufferData(gl.ARRAY_BUFFER, jsonFrame["vehicles"].length * 32, gl.STATIC_DRAW);
    for (i in jsonFrame["vehicles"]) {
      const vehicle = jsonFrame["vehicles"][i];

      const vehicleLoc = vec2.fromValues(vehicle["loc"]["x"], vehicle["loc"]["y"]);
      // Positions for the object
      let positions = [
        vec2.fromValues(0.2, 0.1),
        vec2.fromValues(-0.2, 0.1),
        vec2.fromValues(0.2, -0.1),
        vec2.fromValues(-0.2, -0.1)
      ];
      for (j in positions) {
        vec2.add(positions[j], positions[j], vehicleLoc);
        vec2.rotate(positions[j], positions[j], vehicleLoc, glMatrix.glMatrix.toRadian(vehicle["direction"]));
      }

      let coords = new Float32Array(8);
      // 2 because there are 2 coordinates for every point (2D)
      positions.forEach((item, j) => {
        coords.set(item, j * 2);
      });
      // Store positions into the buffer
      gl.bufferSubData(gl.ARRAY_BUFFER, i * 32, coords);
    }
  }

  function initBuffers(gl) {
    const positionBuffer = gl.createBuffer();

    // Set positionBuffer as the one to apply buffer operations to
    gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);

    storeToBuffer(gl, positionBuffer);

    return {
      position: positionBuffer,
    };
  }

  function drawScene(gl, programInfo, buffers, currTime, dTime) {
    gl.clearColor(1.0, 1.0, 1.0, 1.0); // Clear to black, fully opaque
    gl.clearDepth(1.0);                // Clear everything
    gl.enable(gl.DEPTH_TEST);          // Enable depth testing
    gl.depthFunc(gl.LEQUAL);           // Near things obscure far things

    // Clear the canvas before drawing
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

    const projectionMatrix = mat4.create();
    // Create a perspective matrix for the camera
    ///*
    const fieldOfView = 90 * Math.PI / 180; // in radians
    const aspect = gl.canvas.clientWidth / gl.canvas.clientHeight;
    const zNear = 0.01;
    const zFar = 100.0;

    mat4.perspective(projectionMatrix, fieldOfView, aspect, zNear, zFar);
    //*/

    // Set drawing position to the "identity" point (center of the scene)
    const modelViewMatrix = mat4.create();

    mat4.translate(modelViewMatrix,    // destination matrix
                   modelViewMatrix,    // matrix to translate
                   [-0.0, 0.0, -1.0]); // amount to translate

    {
      const numComponents = 2;
      const type = gl.FLOAT;
      const normalize = false;
      const stride = 0;
      const offset = 0;
      gl.bindBuffer(gl.ARRAY_BUFFER, buffers.position);
      gl.vertexAttribPointer(
        programInfo.attribLocations.vertexPosition,
        numComponents,
        type,
        normalize,
        stride,
        offset);
      gl.enableVertexAttribArray(programInfo.attribLocations.vertexPosition);
    }

    // Tell WebGL to use our program when drawing
    gl.useProgram(programInfo.program);

    // Set the shader uniforms
    gl.uniformMatrix4fv(
      programInfo.uniformLocations.projectionMatrix,
      false,
      projectionMatrix);
    gl.uniformMatrix4fv(
      programInfo.uniformLocations.modelViewMatrix,
      false,
      modelViewMatrix);

    {
      const vertexCount = 4;
      // Get the size of the buffer and check that it's valid
      const bufSize = gl.getBufferParameter(gl.ARRAY_BUFFER, gl.BUFFER_SIZE);
      if (!Number.isInteger(bufSize / 32)) {
        console.log("WARNING: Buffer is not a valid size!");
      }
      // Draw vertices on the screen
      for (let i = 0; i < bufSize / 32; i++) {
        gl.drawArrays(gl.TRIANGLE_STRIP, i * 4, vertexCount);
      }
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
