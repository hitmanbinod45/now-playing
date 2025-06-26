<script>
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	
	let isListening = false;
	let mediaRecorder = null;
	let websocket = null;
	let currentSong = null;
	let confidence = 0;
	let audioChunks = [];
	let stream = null;
	
	// Audio visualization
	let canvas;
	let canvasContext;
	let audioContext;
	let analyser;
	let dataArray;
	let animationId;
	
	onMount(() => {
		if (browser) {
			// Initialize canvas for audio visualization
			canvas = document.getElementById('audioCanvas');
			canvasContext = canvas.getContext('2d');
		}
	});
	
	async function startListening() {
		if (!browser) return;
		
		try {
			// Get microphone access
			stream = await navigator.mediaDevices.getUserMedia({ 
				audio: {
					sampleRate: 22050,
					channelCount: 1
				}
			});
			
			// Setup audio visualization
			audioContext = new (window.AudioContext || window.webkitAudioContext)();
			const source = audioContext.createMediaStreamSource(stream);
			analyser = audioContext.createAnalyser();
			analyser.fftSize = 256;
			
			const bufferLength = analyser.frequencyBinCount;
			dataArray = new Uint8Array(bufferLength);
			
			source.connect(analyser);
			
			// Start visualization
			drawVisualization();
			
			// Setup WebSocket connection
			websocket = new WebSocket('ws://localhost:8000/ws/listen');
			
			websocket.onopen = () => {
				console.log('WebSocket connected');
			};
			
			websocket.onmessage = (event) => {
				const data = JSON.parse(event.data);
				
				if (data.type === 'match_found') {
					currentSong = data.song;
					confidence = 0.85; // Mock confidence
					stopListening();
				}
			};
			
			// Setup media recorder for audio streaming
			mediaRecorder = new MediaRecorder(stream, {
				mimeType: 'audio/webm'
			});
			
			mediaRecorder.ondataavailable = (event) => {
				if (event.data.size > 0 && websocket.readyState === WebSocket.OPEN) {
					// Convert to ArrayBuffer and send
					event.data.arrayBuffer().then(buffer => {
						websocket.send(buffer);
					});
				}
			};
			
			mediaRecorder.start(1000); // Send data every second
			isListening = true;
			
		} catch (error) {
			console.error('Error starting audio capture:', error);
			alert('Please allow microphone access to identify songs');
		}
	}
	
	function stopListening() {
		isListening = false;
		
		if (mediaRecorder && mediaRecorder.state !== 'inactive') {
			mediaRecorder.stop();
		}
		
		if (stream) {
			stream.getTracks().forEach(track => track.stop());
		}
		
		if (websocket) {
			websocket.close();
		}
		
		if (audioContext) {
			audioContext.close();
		}
		
		if (animationId) {
			cancelAnimationFrame(animationId);
		}
	}
	
	function drawVisualization() {
		if (!analyser || !canvasContext) return;
		
		animationId = requestAnimationFrame(drawVisualization);
		
		analyser.getByteFrequencyData(dataArray);
		
		canvasContext.fillStyle = 'rgba(0, 0, 0, 0.1)';
		canvasContext.fillRect(0, 0, canvas.width, canvas.height);
		
		const barWidth = (canvas.width / dataArray.length) * 2.5;
		let barHeight;
		let x = 0;
		
		for (let i = 0; i < dataArray.length; i++) {
			barHeight = (dataArray[i] / 255) * canvas.height * 0.8;
			
			const r = barHeight + 25 * (i / dataArray.length);
			const g = 250 * (i / dataArray.length);
			const b = 50;
			
			canvasContext.fillStyle = `rgb(${r},${g},${b})`;
			canvasContext.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
			
			x += barWidth + 1;
		}
	}
	
	function resetSearch() {
		currentSong = null;
		confidence = 0;
	}
</script>

<svelte:head>
	<title>What's This Song?</title>
</svelte:head>

<div class="min-h-screen flex flex-col items-center justify-center p-4 text-white">
	<!-- Header -->
	<div class="text-center mb-8">
		<h1 class="text-4xl md:text-6xl font-bold mb-4 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
			What's This Song?
		</h1>
		<p class="text-lg text-gray-300">
			Tap to identify any song playing around you
		</p>
	</div>
	
	<!-- Main Interface -->
	<div class="relative">
		<!-- Audio Visualization Canvas -->
		<canvas 
			id="audioCanvas" 
			width="300" 
			height="200" 
			class="absolute inset-0 rounded-full opacity-70"
			class:hidden={!isListening}
		></canvas>
		
		<!-- Listen Button -->
		<button
			on:click={isListening ? stopListening : startListening}
			class="relative w-64 h-64 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 
				   hover:from-purple-600 hover:to-pink-600 transform hover:scale-105 
				   transition-all duration-300 shadow-2xl flex items-center justify-center
				   {isListening ? 'animate-pulse' : ''}"
			disabled={isListening && !currentSong}
		>
			<div class="text-center">
				{#if isListening && !currentSong}
					<div class="text-2xl mb-2">🎵</div>
					<div class="text-lg font-semibold">Listening...</div>
				{:else if currentSong}
					<div class="text-2xl mb-2">✨</div>
					<div class="text-lg font-semibold">Found It!</div>
				{:else}
					<div class="text-3xl mb-2">🎧</div>
					<div class="text-xl font-semibold">Tap to Listen</div>
				{/if}
			</div>
		</button>
	</div>
	
	<!-- Song Result -->
	{#if currentSong}
		<div class="mt-8 bg-white/10 backdrop-blur-md rounded-2xl p-6 max-w-md w-full text-center">
			<h2 class="text-2xl font-bold mb-2">{currentSong.title}</h2>
			<p class="text-lg text-gray-300 mb-4">by {currentSong.artist}</p>
			
			<!-- Confidence Score -->
			<div class="mb-4">
				<div class="text-sm text-gray-400 mb-1">Confidence</div>
				<div class="w-full bg-gray-700 rounded-full h-2">
					<div 
						class="bg-gradient-to-r from-green-400 to-blue-500 h-2 rounded-full transition-all duration-1000"
						style="width: {confidence * 100}%"
					></div>
				</div>
				<div class="text-sm mt-1">{Math.round(confidence * 100)}%</div>
			</div>
			
			<!-- Action Buttons -->
			<div class="flex gap-3 justify-center">
				<button 
					class="px-6 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors"
					on:click={() => window.open(`https://open.spotify.com/search/${encodeURIComponent(currentSong.title + ' ' + currentSong.artist)}`, '_blank')}
				>
					🎵 Spotify
				</button>
				<button 
					class="px-6 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
					on:click={() => window.open(`https://music.youtube.com/search?q=${encodeURIComponent(currentSong.title + ' ' + currentSong.artist)}`, '_blank')}
				>
					▶️ YouTube
				</button>
			</div>
			
			<button 
				on:click={resetSearch}
				class="mt-4 px-6 py-2 bg-gray-600 hover:bg-gray-700 rounded-lg transition-colors"
			>
				🔄 Search Again
			</button>
		</div>
	{/if}
	
	<!-- Features -->
	<div class="mt-12 text-center max-w-2xl">
		<h3 class="text-xl font-semibold mb-4">How It Works</h3>
		<div class="grid md:grid-cols-3 gap-6 text-sm">
			<div class="bg-white/5 rounded-lg p-4">
				<div class="text-2xl mb-2">🎤</div>
				<div class="font-medium mb-1">Listen</div>
				<div class="text-gray-400">Capture audio from your surroundings</div>
			</div>
			<div class="bg-white/5 rounded-lg p-4">
				<div class="text-2xl mb-2">🔍</div>
				<div class="font-medium mb-1">Analyze</div>
				<div class="text-gray-400">Extract unique audio fingerprints</div>
			</div>
			<div class="bg-white/5 rounded-lg p-4">
				<div class="text-2xl mb-2">✨</div>
				<div class="font-medium mb-1">Identify</div>
				<div class="text-gray-400">Match against music database</div>
			</div>
		</div>
	</div>
</div>

<style>
	@import '@tailwindcss/base';
	@import '@tailwindcss/components';
	@import '@tailwindcss/utilities';
</style>