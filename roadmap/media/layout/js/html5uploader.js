(
  function() {
    FileUpload = {
		is_chrome: navigator.userAgent.toLowerCase().indexOf('chrome') > -1,

		getSplitter: function(text) {
			return (text.indexOf('?') != -1) ? '&' : '?';
		},

		upload: function(file, status) {
			/*
			Firefox 3.6, Chrome 6, WebKit
			*/
			if(window.FileReader) {
				this.loadEnd = function() {
					bin = reader.result;
					xhr = new XMLHttpRequest();
					xhr.open('POST', uploadFileURL + getSplitter(uploadFileURL) +  'up=true', true);

					var boundary = 'xxxxxxxxx';
					var body = '--' + boundary + "\r\n";
					body += "Content-Disposition: form-data; name=attachFile; filename='" + file.name + "'\r\n";
					body += "Content-Type: application/octet-stream\r\n\r\n";
					body += bin + "\r\n";
					body += '--' + boundary + '--';

					xhr.setRequestHeader('content-type', 'multipart/form-data; boundary=' + boundary);
					/*
					Firefox 3.6
					*/
					if(xhr.sendAsBinary != null) {
						xhr.sendAsBinary(body);
						/*
						Chrome 7 needs to base64 uncode
						*/
					} else {
						xhr.open('POST', uploadFileURL +  getSplitter(uploadFileURL) + 'up=true&base64=true', true);
						xhr.setRequestHeader('UP-FILENAME', file.name);
						xhr.setRequestHeader('UP-SIZE', file.size);
						xhr.setRequestHeader('UP-TYPE', file.type);
						data_send = window.btoa(bin);
						xhr.send(data_send);
					}
					if (show) {
						var newFile  = document.createElement('div');
						newFile.innerHTML = 'Loaded : '+file.name+' size '+file.size+' B';
					}
					if (status) {
						document.getElementById(status).innerHTML = 'Loaded : 100%';
					}
				}

				/*
				File load failure
				*/
				this.loadError = function(event) {
					switch(event.target.error.code) {
						case event.target.error.NOT_FOUND_ERR:
							document.getElementById(status).innerHTML = 'File not found!';
						break;
						case event.target.error.NOT_READABLE_ERR:
							document.getElementById(status).innerHTML = 'File not readable!';
						break;
						case event.target.error.ABORT_ERR:
						break;
						default:
							document.getElementById(status).innerHTML = 'Read error.';
					}
				}

				/*
				Reading Progress
				*/
				this.loadProgress = function(event) {
					if (event.lengthComputable) {
						var percentage = Math.round((event.loaded * 100) / event.total);
						document.getElementById(status).innerHTML = 'Loaded : '+percentage+'%';
						if(event.loaded == event.total) {
							finished(file.name);
						}
					}
				}

			reader = new FileReader();
			/*
			Firefox 3.6, WebKit
			*/
			if(reader.addEventListener) {
				reader.addEventListener('loadend', this.loadEnd, false);
				if (status != null)
				{
					reader.addEventListener('error', this.loadError, false);
					reader.addEventListener('progress', this.loadProgress, false);
				}

			/*
			Chrome 7
			*/
			} else {
				reader.onloadend = this.loadEnd;
				if (status != null)
				{
					reader.onerror = this.loadError;
					reader.onprogress = this.loadProgress;
				}
			}
			var preview = new FileReader();
			/*
			Firefox 3.6, WebKit
			*/
			if(preview.addEventListener) {
				preview.addEventListener('loadend', this.previewNow, false);
			/*
			Chrome 7
			*/
			} else {
				preview.onloadend = this.previewNow;
			}

			/*
			START READING
			*/
			reader.readAsBinaryString(file);

			/*
			Preview uploaded files
			*/
			if (show) {
				preview.readAsDataURL(file);
			}

			/*
			Safari 5
			*/
			} else {
				xhr = new XMLHttpRequest();
				xhr.open('POST', uploadFileURL + getSplitter(uploadFileURL) + 'up=true', true);
				xhr.setRequestHeader('UP-FILENAME', file.name);
				xhr.setRequestHeader('UP-SIZE', file.size);
				xhr.setRequestHeader('UP-TYPE', file.type);
				xhr.send(file);

				if (status) {
					document.getElementById(status).innerHTML = 'Loaded : 100%';
				}
				if (show) {
					var newFile  = document.createElement('div');
					newFile.innerHTML = 'Loaded : '+file.name+' size '+file.size+' B';
					document.getElementById(show).appendChild(newFile);
				}
			}
		},


		initialise: function(dropElement, uploadFileURL, finished, status) {
			/*
			Add event listeners to the DOM element
			*/
			dropElement.get(0).addEventListener("dragover", function(event) {
				event.stopPropagation();
				event.preventDefault();
			}, true);
			dropElement.get(0).addEventListener("drop", function(event) {
				event.preventDefault();
				var dt = event.dataTransfer;
				var files = dt.files;
				for (var i = 0; i<files.length; i++) {
					var file = files[i];
					upload(file, status);
				}
			}, false);
		}
    }
  }
)();








function uploader(place, status, uploadFileURL, show, finished) {
	// Function drop file
	this.drop = function(event) {
		event.preventDefault();
	 	var dt = event.dataTransfer;
	 	var files = dt.files;
	 	for (var i = 0; i<files.length; i++) {
			var file = files[i];
			upload(file);
	 	}
	}

	// The inclusion of the event listeners (DragOver and drop)

	this.uploadPlace =  document.getElementById(place);
	this.uploadPlace.addEventListener("dragover", function(event) {
		event.stopPropagation();
		event.preventDefault();
	}, true);
	this.uploadPlace.addEventListener("drop", this.drop, false);
}
