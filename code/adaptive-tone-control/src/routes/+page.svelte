<!-- src/routes/+page.svelte -->
<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import FileUploader from '../components/FileUploader.svelte';
  import Knob from '../components/Knob.svelte';
  import Visualizer from '../components/Visualizer.svelte';
  import { AudioProcessor } from '../lib/audio.js';

  let audioProcessor: AudioProcessor;
  let audio: HTMLAudioElement | null = null;
  let isPlaying: boolean = false;

  let lowGain: number = 1;
  let midGain: number = 1;
  let highGain: number = 1;

  let frequencyData = {
    low: 0,
    mid: 0,
    high: 0
  };

  let animationFrame: number;

  onMount(async () => {
    audioProcessor = new AudioProcessor();
  });

  async function handleFileSelected(event: CustomEvent<File>) {
    const file = event.detail;
    if (audio) {
      audio.pause();
      audio.src = '';
      audio = null;
    }
    audio = await audioProcessor.loadAudio(file);
    await audioProcessor.connectAudio(audio);
    audio.play();
    isPlaying = true;
    audioProcessor.setGains(lowGain, midGain, highGain);
    monitorAudio();
  }

  function monitorAudio() {
    if (!audioProcessor || !audio) return;

    function update() {
      frequencyData = audioProcessor.getFrequencyData();
      animationFrame = requestAnimationFrame(update);
    }

    update();
  }

  function togglePlay() {
    if (audio) {
      if (isPlaying) {
        audio.pause();
      } else {
        audio.play();
      }
      isPlaying = !isPlaying;
    }
  }

  function handleLowChange(event: CustomEvent<number>) {
    lowGain = event.detail;
    audioProcessor.setGains(lowGain, midGain, highGain);
  }

  function handleMidChange(event: CustomEvent<number>) {
    midGain = event.detail;
    audioProcessor.setGains(lowGain, midGain, highGain);
  }

  function handleHighChange(event: CustomEvent<number>) {
    highGain = event.detail;
    audioProcessor.setGains(lowGain, midGain, highGain);
  }

  onDestroy(() => {
    if (animationFrame) {
      cancelAnimationFrame(animationFrame);
    }
    if (audio) {
      audio.pause();
    }
  });
</script>

<style>
  .controls {
    display: flex;
    justify-content: center;
    gap: 2rem;
    margin-top: 2rem;
    flex-wrap: wrap;
  }

  .knob-container {
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .knob-label {
    margin-top: 1rem;
    font-weight: bold;
  }

  .player-controls {
    display: flex;
    justify-content: center;
    margin-top: 2rem;
  }

  .play-button {
    padding: 0.75rem 1.5rem;
    background-color: #10b981; /* emerald-500 */
    color: white;
    border: none;
    border-radius: 0.5rem;
    font-size: 1rem;
    cursor: pointer;
    transition: background-color 0.3s;
  }

  .play-button:hover {
    background-color: #059669; /* emerald-600 */
  }
</style>

<div class="container mx-auto p-4">
  <h1 class="text-3xl font-bold text-center mb-6">Adaptive Tone Control</h1>

  <FileUploader on:fileSelected={handleFileSelected} />

  {#if audio}
    <div class="player-controls">
      <button class="play-button" on:click={togglePlay}>
        {isPlaying ? 'Pause' : 'Play'}
      </button>
    </div>

    <div class="controls">
      <div class="knob-container">
        <Knob
          value={lowGain}
          min={0}
          max={2}
          step={0.1}
          size={100}
          on:change={handleLowChange}
        />
        <span class="knob-label">Low</span>
      </div>
      <div class="knob-container">
        <Knob
          value={midGain}
          min={0}
          max={2}
          step={0.1}
          size={100}
          on:change={handleMidChange}
        />
        <span class="knob-label">Mid</span>
      </div>
      <div class="knob-container">
        <Knob
          value={highGain}
          min={0}
          max={2}
          step={0.1}
          size={100}
          on:change={handleHighChange}
        />
        <span class="knob-label">High</span>
      </div>
    </div>

    <Visualizer {frequencyData} />
  {/if}
</div>
