<script>
  import { onMount } from 'svelte';
  import { recordAudio } from '$lib/utils/audioRecorder.js';
  
  export let isRecording = false;
  export let onRecordingChange;
  export let onResults;
  
  let audioContext;
  let mediaRecorder;
  let audioChunks = [];
  
  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];
    
    mediaRecorder.ondataavailable = (e) => {
      audioChunks.push(e.data);
    };
    
    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
      await sendToBackend(audioBlob);
      stream.getTracks().forEach(track => track.stop());
    };
    
    mediaRecorder.start();
    onRecordingChange(true);
  };
  
  const stopRecording = () => {
    mediaRecorder.stop();
    onRecordingChange(false);
  };
  
  const sendToBackend = async (blob) => {
    const formData = new FormData();
    formData.append('audio', blob, 'recording.webm');
    
    const response = await fetch('http://localhost:8000/identify', {
      method: 'POST',
      body: formData
    });
    
    const data = await response.json();
    onResults(data);
  };
</script>

<button
  on:click={isRecording ? stopRecording : startRecording}
  class="w-full py-3 px-4 rounded-md text-white font-medium transition-colors
         {isRecording 
           ? 'bg-red-500 hover:bg-red-600' 
           : 'bg-blue-500 hover:bg-blue-600'}"
>
  {isRecording ? 'Stop Recording' : 'Identify Song'}
</button>