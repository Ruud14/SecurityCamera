window.onload = function(){
		var jmuxer = new JMuxer({
			node: 'stream',
			mode: 'video',
			flushingTime: 0,
			fps: $fps,
			debug: false
		 });

		var ws = new WebSocket("ws://$ip:$port/ws/");
		ws.binaryType = 'arraybuffer';
		ws.addEventListener('message',function(event){
			if (!document.hidden){
				jmuxer.feed({
					video: new Uint8Array(event.data)
				});
			}
		});
	}