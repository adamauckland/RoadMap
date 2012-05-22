(
function () {
	Chat = {
		setStatus: function (status) {
			$.get('/roadmap/chat/set_chat_status?chat_status=' + status, function (data) {
				Properties.chatStatus = status;
			});
		},

		setChattingWith: function (status) {
			$.get('/roadmap/chat/set_chatting_with?chatting_with=' + status, function (data) {
				Properties.chattingWith = status;
			});
		},

		pollChat: function () {
			if (Properties.chattingWith != null) {

				$.get('/roadmap/chat/chat_core?user_id=' + Properties.chattingWith, function (data) {
					$('#chatCore').html(data);
					//$("#chatRetainer").animate({ scrollTop: $("#chatRetainer").attr("scrollHeight") - $('#chatRetainer').height() }, 100);
					$("#chatRetainer").animate({
						scrollTop: $("#chatRetainer").attr("scrollHeight") - $('#chatRetainer').height()
					}, 10);
				});
			}

			window.setTimeout(Chat.pollChat, 2000);
		},

		chatSwitch: function (id) {
			$('#chatAvailableUsers').hide();
			$('#messageBox').show();
			Chat.setChattingWith(id);
			Chat.setStatus(2);
			return false;
		},

		initialiseChat: function () {
			$('#user-controls #userName').bind('click', function () {
				switch (Properties.chatStatus) {
				case 0:
					Chat.setStatus(1);
					$('#chatAvailableUsers').show('slide', {
						direction: 'up'
					}, 250);
					break;

				case 1:
					Chat.setStatus(0);
					$('#chatAvailableUsers').hide('slide', {
						direction: 'up'
					}, 250);
					break;

				case 2:
					Chat.setStatus(1);
					$('#messageBox').hide('slide', {
						direction: 'up'
					}, 250);
					$('#chatAvailableUsers').show('slide', {
						direction: 'up'
					}, 250);
					break;
				}


			});

			$('#chatPost').bind('click', function () {
				$.post('/roadmap/chat/chat_post', {
					user_to: Properties.chattingWith,
					message: $('#chatMessage').val()
				}, function (data) {
					if (data == 'success') {
						$('#chatMessage').val('');
					}
				});
			});

			Chat.pollChat();
		}
	}
});