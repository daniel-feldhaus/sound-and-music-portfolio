// src/lib/audio.ts
export class AudioProcessor {
  audioContext: AudioContext;
  source: MediaElementAudioSourceNode | null = null;
  workletNode: AudioWorkletNode | null = null;
  analyser: AnalyserNode;
  frequencyData: Uint8Array;

  constructor() {
    this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    this.analyser = this.audioContext.createAnalyser();
    this.analyser.fftSize = 1024;
    this.frequencyData = new Uint8Array(this.analyser.frequencyBinCount);
  }

  async loadAudio(file: File): Promise<HTMLAudioElement> {
    const url = URL.createObjectURL(file);
    const audio = new Audio();
    audio.src = url;
    audio.crossOrigin = "anonymous";
    audio.load();

    return new Promise((resolve, reject) => {
      audio.onloadedmetadata = () => {
        resolve(audio);
      };
      audio.onerror = () => {
        reject(new Error("Failed to load audio."));
      };
    });
  }

  async connectAudio(audio: HTMLAudioElement) {
    await this.audioContext.audioWorklet.addModule('/worklets/fft-processor.js');
    this.workletNode = new AudioWorkletNode(this.audioContext, 'fft-processor');

    this.source = this.audioContext.createMediaElementSource(audio);
    this.source.connect(this.workletNode).connect(this.analyser).connect(this.audioContext.destination);
  }

  setGains(low: number, mid: number, high: number) {
    if (this.workletNode) {
      this.workletNode.port.postMessage({
        type: 'setGains',
        value: { low, mid, high }
      });
    }
  }

  getFrequencyData() {
    this.analyser.getByteFrequencyData(this.frequencyData);
    // Calculate average energies for low, mid, high
    const sampleRate = this.audioContext.sampleRate;
    const fftSize = this.analyser.fftSize;
    const freqStep = sampleRate / fftSize;

    let lowSum = 0;
    let midSum = 0;
    let highSum = 0;
    let lowCount = 0;
    let midCount = 0;
    let highCount = 0;

    this.frequencyData.forEach((value, index) => {
      const freq = index * freqStep;
      if (freq >= 0 && freq < 300) {
        lowSum += value;
        lowCount++;
      } else if (freq >= 300 && freq < 2000) {
        midSum += value;
        midCount++;
      } else if (freq >= 2000) {
        highSum += value;
        highCount++;
      }
    });

    const lowAvg = lowCount ? lowSum / lowCount : 0;
    const midAvg = midCount ? midSum / midCount : 0;
    const highAvg = highCount ? highSum / highCount : 0;

    return {
      low: lowAvg,
      mid: midAvg,
      high: highAvg
    };
  }
}
