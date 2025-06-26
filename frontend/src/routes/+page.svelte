<script>
  import RecordButton from '$lib/components/RecordButton.svelte'
  import ResultsCard from '$lib/components/ResultsCard.svelte'
  
  let isRecording = false;
  let results = null;
  
  const handleRecording = (status) => {
    isRecording = status;
  };
  
  const handleResults = (data) => {
    results = data;
  };
</script>

<main class="min-h-screen bg-gray-100 p-4">
  <div class="max-w-md mx-auto bg-white rounded-xl shadow-md p-6">
    <h1 class="text-2xl font-bold text-center mb-6">What's This Song?</h1>
    
    <RecordButton 
      {isRecording} 
      onRecordingChange={handleRecording}
      onResults={handleResults}
    />
    
    {#if results}
      <ResultsCard {results} />
    {/if}
  </div>
</main>