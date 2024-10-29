// public/worklets/fft-processor.js

importScripts('https://cdn.jsdelivr.net/npm/fft.js/dist/fft.min.js');

class FFTProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.fftSize = 1024; // Must match the analyser.fftSize
    this.fft = new FFT(this.fftSize);
    this.inputBuffer = new Float32Array(this.fftSize);
    this.outputBuffer = new Float32Array(this.fftSize);
    this.lowGain = 1.0;
    this.midGain = 1.0;
    this.highGain = 1.0;

    // Listen for messages from the main thread
    this.port.onmessage = (event) => {
      const { type, value } = event.data;
      if (type === 'setGains') {
        this.lowGain = value.low;
        this.midGain = value.mid;
        this.highGain = value.high;
      }
    };
  }

  process(inputs, outputs, parameters) {
    const input = inputs[0];
    const output = outputs[0];

    if (input.length > 0) {
      const inputChannel = input[0];
      const outputChannel = output[0];

      for (let i = 0; i < inputChannel.length; i++) {
        this.inputBuffer[i] = inputChannel[i];
      }

      // Perform FFT
      const real = this.inputBuffer.slice();
      const imag = new Float32Array(this.fftSize);
      this.fft.realTransform(real, imag);
      this.fft.completeSpectrum(real, imag);

      // Apply gains to frequency bands
      const sampleRate = 44100; // Assuming 44.1kHz; adjust if different
      const freqStep = sampleRate / this.fftSize;

      for (let k = 0; k < this.fftSize / 2; k++) {
        const freq = k * freqStep;
        if (freq < 300) {
          real[k] *= this.lowGain;
          imag[k] *= this.lowGain;
        } else if (freq >= 300 && freq < 2000) {
          real[k] *= this.midGain;
          imag[k] *= this.midGain;
        } else {
          real[k] *= this.highGain;
          imag[k] *= this.highGain;
        }
      }

      // Perform IFFT
      const inverseReal = new Float32Array(this.fftSize);
      const inverseImag = new Float32Array(this.fftSize);
      this.fft.inverseTransform(inverseReal, inverseImag, real, imag);

      // Normalize and write to output
      for (let i = 0; i < this.fftSize; i++) {
        outputChannel[i] = inverseReal[i] / this.fftSize;
      }
    }

    return true; // Keep the processor alive
  }
}

registerProcessor('fft-processor', FFTProcessor);
