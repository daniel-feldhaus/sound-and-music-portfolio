<!-- src/components/FileUploader.svelte -->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  const dispatch = createEventDispatcher();
  let isDragOver = false;

  function handleFileSelect(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      dispatch('fileSelected', input.files[0]);
    }
  }

  function handleDrop(event: DragEvent) {
    event.preventDefault();
    isDragOver = false;
    if (event.dataTransfer && event.dataTransfer.files.length > 0) {
      dispatch('fileSelected', event.dataTransfer.files[0]);
      event.dataTransfer.clearData();
    }
  }

  function handleDragOver(event: DragEvent) {
    event.preventDefault();
    isDragOver = true;
  }

  function handleDragLeave(event: DragEvent) {
    event.preventDefault();
    isDragOver = false;
  }

  function handleKeyPress(event: KeyboardEvent) {
    if (event.key === 'Enter' || event.key === ' ') {
      const input = document.querySelector('.uploader input[type="file"]') as HTMLInputElement;
      input.click();
    }
  }
</script>

<style>
  .uploader {
    border: 2px dashed #bbb;
    border-radius: 8px;
    padding: 40px;
    text-align: center;
    transition: border-color 0.3s, background-color 0.3s;
    cursor: pointer;
  }

  .uploader.dragover {
    border-color: #333;
    background-color: #f0f0f0;
  }
</style>

<div
  class="uploader {isDragOver ? 'dragover' : ''}"
  role="button"
  aria-label="File uploader"
  tabindex="0"
  on:drop={handleDrop}
  on:dragover={handleDragOver}
  on:dragleave={handleDragLeave}
  on:click={() => {
    const input = document.querySelector('.uploader input[type="file"]') as HTMLInputElement;
    input.click();
  }}
  on:keypress={handleKeyPress}
>
  <p>Drag & Drop an audio file here or click to select</p>
  <input
    type="file"
    accept="audio/*"
    class="hidden"
    on:change={handleFileSelect}
  />
</div>
