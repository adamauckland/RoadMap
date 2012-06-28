/** @namespace
 *
 */
(
	function() {
		/**
		 * @namespace
		 */

		Layout = {

			/**
			 * @function
			 * @description Centre an element
			 */

			centreElement: function (item) {
				item.css("position","absolute");
				item.css("top", (($(window).height() - item.outerHeight()) / 2) + $(window).scrollTop() + "px");
				item.css("left", (($(window).width() - item.outerWidth()) / 2) + $(window).scrollLeft() + "px");
			},
		}
	}
)();



/**
 * @namespace
 */
(
function () {

	/**
	 *	@namespace
	 */

	Roadmap = {
		loader: [],
		mainFeed: null,
		closingMenu: null,

		/**
		 *	@function
		 *	@description Add a function to be executed when the document is ready
		 *	@param {function} func The function to be executed
		 */

		addLoader: function (func) {
			Roadmap.loader[Roadmap.loader.length] = func;
		},

		/**
		 *	@namespace
		 *	@description Item grouping.
		 *	Group is a property of an item, not a hierarchical group.
		 */

		grouping: {
			/**
			 * @function
			 * @description Initialise
			 */

			initialise: function() {
				if ($('#assignToGroup').length == 1) {
					var assignToGroup = $('#assignToGroup');
					assignToGroup.find('#assignToGroupCancelButton').click(function() {
						assignToGroup.fadeOut();
					});

					assignToGroup.find('#assignToGroupUpdateButton').click(function() {
						var name = assignToGroup.find('#assignToGroupNewGroup').val().trim();

						if (name == '') {
							return;
						}

						Roadmap.grouping.addToGroupUpdate(name);
					});

					assignToGroup.find('#assignToGroupNewGroup').keyup(function(key) {
						if(key.keyCode == 13) {
							assignToGroup.find('#assignToGroupUpdateButton').click();
						}

						if(key.keyCode == 27) {
							assignToGroup.fadeOut();
						}
					});
				}
			},

			/**
			 *	@function
			 *	@description Add a number of items to the session selected items
			 */

			selectItems: function(link) {
				var groupTr = $(link).parents('tr.itemGroup');

				var nextItem = groupTr.next('tr');
				var buildIds = [];
				while((nextItem.length != 0) && (!nextItem.hasClass('itemGroup'))) {
					var id = nextItem.find('span.itemId').text().replace('#', '');
					buildIds.push(id);
					nextItem = nextItem.next();
				}
				$.post('/roadmap/ledger/select_multiple', {
					'search_ids' : buildIds.join(',')
				}, function(data) {
					window.location.href = window.location.href;
				});
				return false;
			},

			/**
			 *	@function
			 *	@description Add the selected items in the session to the group
			 */

			addToGroup: function() {
				Layout.centreElement($('#assignToGroup'));
				$('#assignToGroup').find('#assignToGroupNewGroup').val('');
				$('#assignToGroup').fadeIn(function() {
					$('#assignToGroup').find('#assignToGroupNewGroup').focus();
				});
				return false;
			},

			/**
			 * @function
			 * @description Send the group to the server to group selected items
			 */

			addToGroupUpdate: function(name) {
				var content = $('#assignToGroupContent');
				var spinner = $('#assignToGroupSpinner');
				spinner.show();
				spinner.css( {
					'left': (content.outerWidth() / 2) - 8,
					'top': (content.outerHeight() / 2) - 8,
				});

				$.post('/roadmap/ledger/selected_to_group', {
					'name': name
				}, function(data) {
					//$('body').load(window.location.href);
					$('#viewSubmitButton').click();
				});
				return false;
			}
		},

		/**
		 * @namespace
		 */

		navigationSearch: {

			/**
			 * @function
			 */

			initialise: function() {
				Roadmap.navigationSearch.setupCheckboxes('.hiddenUserTitle', '.hiddenUser');
				Roadmap.navigationSearch.setupCheckboxes('.hiddenLocationTitle', '.hiddenLocation');
				Roadmap.navigationSearch.setupCheckboxes('.hiddenStateTitle', '.hiddenState');
				Roadmap.navigationSearch.setupCheckboxes('.hiddenTargetTitle', '.hiddenTarget');
			},

			/**
			 * @function
			 * @description Hide any groups of checkboxes where they are all selected
			 */

			setupCheckboxes: function(titleCss, checkboxCss) {
				var allUsersChecked = true;
				$(checkboxCss).each(function(index, element) {
					var lookForCheckbox = $(element).children('input[type=checkbox]');
					if(lookForCheckbox.length == 1) {
						if(!lookForCheckbox.is(':checked')) {
							allUsersChecked = false;
						}
					}
				});
				if(allUsersChecked) {
					/*$(checkboxCss).each(function(index, element) {
						$(element).hide();
					});*/
					$(titleCss).click(function(evt) {
						$(this).hide();
						$(checkboxCss).each(function(index, element) {
							$(element).show();
						});
						return false;
					});
				} else {
					//$(titleCss).hide();
				}
			},
		},

		/**
		 *	@namespace
		 */

		reminders: {
			/**
			 * @function
			 * @description Initialise
			 */

			initialise: function() {
				if ($('#remindMeWhen').length == 1) {
					var remindMeWhen = $('#remindMeWhen');
					remindMeWhen.find('#remindMeWhenCancelButton').click(function() {
						remindMeWhen.fadeOut();
					});

					remindMeWhen.find('#remindMeWhenUpdateButton').click(function() {
						var radioSelected = $('input[name=remindMeWhenRadio]:checked').attr('id');
						var days = remindMeWhen.find('#remindMeWhenDays').val().trim();
						switch (radioSelected) {
							case 'remindMeWhenTomorrow':
								days = 1;
								break;

							case 'remindMeWhenNextWeek':
								days = 'nextweek';
								break;

							case 'remindMeWhenNextMonth':
								days = 'nextmonth';
								break;

							case 'remindMeWhenDaysRadio':
								if (days == '') {
									return false;
								}

								var testDays = parseInt(days);
								if (testDays.toString() != days) {
									return false;
								}
								break;
						}

						Roadmap.reminders.addToReminderUpdate(days);
						return false;
					});

					remindMeWhen.find('#remindMeWhenDays').keyup(function(key) {
						if(key.keyCode == 13) {
							$('#remindMeReason').focus();
						}

						if(key.keyCode == 27) {
							remindMeWhen.fadeOut();
						}
					});
				}
			},

			/**
			 *	@function
			 *	@description Set the session selected items to hidden and remind the user in X days
			 *	@returns false
			 */

			addToReminder: function() {
				var remindMe = $('#remindMeWhen');
				Layout.centreElement(remindMe);
				remindMe.find('#remindMeWhenDays').val('');
				remindMe.fadeIn(function() {
					remindMe.find('#remindMeWhenDays').click(function() {
						remindMe.find('#remindMeWhenDaysRadio').click();
					});
					remindMe.find('#remindMeWhenDays').focus();
				});
				return false;
			},

			/**
			 * @function
			 * @description Send the reminder request to server
			 */

			addToReminderUpdate: function(days) {
				var content = $('#remindMeWhenContent');
				var spinner = $('#remindMeWhenSpinner');
				spinner.show();
				spinner.css( {
					'left': (content.outerWidth() / 2) - 8,
					'top': (content.outerHeight() / 2) - 8,
				});

				$.post('/roadmap/ledger/selected_to_remind', {
					'days': days,
					'comment': $('#remindMeReason').val()
				}, function(data) {
					$('body').load(window.location.href);
				});

				return false;
			}
		},

		/**
		 * 	@function
		 * 	@description Check the feed for new notifications to be popped up using Growl
		 */

		checkFeed: function () {
			var date = new Date();
			var url = '/roadmap/ledger/feed_growl?year='
				+ date.getFullYear() + '&month=' + (date.getMonth() + 1)
				+ '&day=' + (date.getDate()) + '&hour=' + (date.getHours() - 1)
				+ '&minute=' + (date.getMinutes()) + '&second=' + date.getSeconds();

			$.getJSON(url, function (data) {
				if (data === null) {
					return;
				}
				Roadmap.mainFeed = data;
				$.each(data, function (i, item) {
                    // someone has changed the item we're looking at
                    if((item.fields.item.toString() == PageProperties.itemId.toString()))
                    {
                        if(item.fields.author.toString() != PageProperties.userId.toString()) {
                            $('#recordLocking').fadeIn(1000);
                        }
                    }
					$.jGrowl(item.fields.description, {
						header: '',
						position: 'bottom-right',
						speed: 'slow'
					});
				});
			});
			Roadmap.checkFeedTimer();
		},

		/**
		 *	@function
		 */

		checkFeedTimer: function () {
			setTimeout(Roadmap.checkFeed, 5000);
		},

		/**
		 *	@function
		 *	@description Provides a dropdown list of currently active binders to navigate to.
		 *	The list fades out when the mouse leaves the area
		 */

		activeMenu: function () {
			var closingMenu;

			/**
			 *	@event
			 *	@description Show the menu
			 */

			$('#activeMenuItem').bind('click', function () {
				if (closingMenu) {
					window.clearTimeout(closingMenu);
				}

				if ($('#activeMenu').css('display') == 'none') {
					$('#activeMenu').show('slide', {
						direction: 'up'
					}, 150);
				}

				return false;
			});

			/**
			 *	@event
			 *	@description The mouse has left the area, start counting
			 */

			$('#activeMenuItem').bind('mouseleave', function () {
				closingMenu = window.setTimeout(function () {
					if ($('#activeMenu').css('display') != 'none') {
						$('#activeMenu').hide('slide', {
							direction: 'up'
						}, 300);
					}
				}, 1000);
			});

			/**
			 *	@event
			 *	@description The mouse is moving over the area, reset any timer
			 */

			$('#activeMenu').bind('mouseover', function () {
				if (closingMenu) {
					window.clearTimeout(closingMenu);
				}
			});

			/**
			 *	@event
			 *	@description The mouse has left the area, start counting
			 */

			$('#activeMenu').bind('mouseleave', function () {
				closingMenu = window.setTimeout(function () {
					if ($('#activeMenu').css('display') != 'none') {
						$('#activeMenu').hide('slide', {
							direction: 'up'
						}, 300);
					}
				}, 1000);
			});
		},

		/**
		 *	@function
		 */

		popupMenuInitialise: function() {
			$('.popupMenuContainer').each(function(index, element) {
				var clickItem = $(element).find('.popupMenuClick');
				var menuItem = $(element).find('.popupMenu');

				Roadmap.popupMenu(clickItem, menuItem);
			});

			var viewSettingsTrigger = $('#viewSettingsTrigger');
			if (viewSettingsTrigger.length == 1) {
				Roadmap.popupMenu(viewSettingsTrigger, $('#viewSettingsPopup'));
			}
		},

		/**
		 *	@function
		 *	@description Popup menu which fades out when the mouse leaves it
		 */

		popupMenu: function (clickItem, menuItem) {
			var closingMenu;
			menuItem.hide();

			/**
			 * @function
			 */

			function disintegrate(element) {
				if (element.css('display') != 'none') {
					element.fadeOut(300);
				}
			}

			/**
			 *	@event
			 */

			clickItem.bind('click', function () {
				if (closingMenu) {
					window.clearTimeout(closingMenu);
				}

				if (menuItem.css('display') == 'none') {
					var position = clickItem.position();
					var leftPosition = position.left - (menuItem.innerWidth() / 4);
					var topPosition = position.top - (menuItem.innerHeight() / 2);

					if(topPosition < 50)
						topPosition = 50;

					menuItem.css(
						{
							'left': leftPosition,
							'top': topPosition,
							'position': 'absolute'
						}
					);
					menuItem.fadeIn(200);
				}

				return false;
			});

			/**
			 *	@event
			 */

			clickItem.bind('mouseleave', function () {
				closingMenu = window.setTimeout(function () {
					disintegrate(menuItem);
				}, 1000);
			});

			/**
			 *	@event
			 */

			menuItem.bind('mouseover', function () {
				if (closingMenu) {
					window.clearTimeout(closingMenu);
				}
			});

			/**
			 *	@event
			 */

			menuItem.bind('mouseleave', function () {
				closingMenu = window.setTimeout(function () {
					disintegrate(menuItem);
				}, 1000);
			});
		},

		/**
		 *	@function
		 *	@description Hide the preview window
		 */

		hidePreview: function() {
			$('#previewWrap').hide();
			$('#activeList tr.preview').each(function(index, element) {
				$(element).removeClass('preview');
			});
		},

		/**
		 *	@function
		 *	@description Show a preview of the item on hover when viewing items list
		 */

		activeItemsHover: function() {
			var activeItemsTimer = null;

			/**
			 *	@private
			 * 	@function
			 * 	Preview Icon - hover in delegate
			 */

			var hoverIn = function(eventItem) {
				if (activeItemsTimer != null) {
					window.clearTimeout(activeItemsTimer);
				}
				var previewContent = $('#previewContent');
				var tr = $(this).parent().parent();
				var id = tr.find('span.itemId a').html().replace('#', '');

				$.get('/roadmap/ledger/preview/'+ id, function(data) {
					$('#innerContent').html(data);

					var position = tr.offset();
					var newTop = position.top - $(window).scrollTop() - 24;
					var maxTop = $(window).height();// + $(window).scrollTop();

					if(newTop < 0) {
						newTop = 0;
					}
					var checkOverspill = parseInt(newTop) + parseInt(previewContent.height());
					if(checkOverspill > maxTop) {
						newTop = parseInt(maxTop) - parseInt(previewContent.height());
					}

					$('#previewContent').css(
						{ top: newTop + 'px'}
					);

					if($('#previewWrap').is(':hidden')) {
						$('#previewWrap').fadeIn(350);
					};
				});

				$('#activeList tr.preview').each(function(index, element) {
					$(element).removeClass('preview');
				});

				tr.addClass('preview');
			};

			/**
			 *	@event
			 *	@description Preview Icon - mouse out delegate
			 */

			var hoverOut = function(eventItem) {
				activeItemsTimer = window.setTimeout(function() {
					$('#previewWrap').fadeOut(500);
					$('#activeList tr.preview').each(function(index, element) {
						$(element).removeClass('preview');
					});
				}, 2000);
			};

			/**
			 *	@event
			 *	@description Preview Icon - click delegate
			 */

			var clickIcon = function(eventItem) {
				$(this).parent()
					.parent()
					.find('input[type="checkbox"]')
					.click();
			};


			$('#activeList tr.instaFilterThis').each(function(index, element) {
				$(element).find('td img.previewThis')
					.hover(hoverIn, hoverOut)
					.click(clickIcon);
			});

			/**
			 *	@event
			 */

			$('#previewWrap').hover(function() {
				if (activeItemsTimer != null) {
					window.clearTimeout(activeItemsTimer);
				}
			}, hoverOut);
		},

		/**
		 *	@function
		 *	@description Order the current viewed items by the selected field.
		 *	This function works by examining the querystring, then looking for the 'order_by' key
		 *	which it replaces with the new field.
		 *
		 *	This is due to the variable quertystring parameters Roadmap uses.
		 *
		 *	@param {String} field The fieldname to order by
		 *
		 */

		activeItemsOrder: function (field) {
			var href = window.location.href;

			if (href.indexOf('?') == -1) {
				href += '?order_by=' + field;
			} else {
				var path = href.split('?')[0];
				var querystring = href.split('?')[1];
				var split_qs = querystring.split('&');
				var new_qs = new Array();

				for (var i in split_qs) {
					var loop_bit = split_qs[i];

					var key = loop_bit.split('=')[0];
					var value = loop_bit.split('=')[1];

					if (key != 'order_by') {
						new_qs.push(loop_bit);
					}
				}
				new_qs.push('order_by=' + field);
				href = path + '?' + new_qs.join('&');
			}

			window.location.href = href;
			return false;
		},

		/**
		 * @function
		 * @description Handle when a checkbox in the item list has been clicked
		 *
		 */

		itemCheckboxClicked: function(url, item) {
			Roadmap.itemCheckboxMenuAppear(function() {
				$.get(url + '?checked=' + $(item).attr('checked'), function(data) {
					$('#selectedItems').html(data);
				});
			});
		},

		/**
		 * @function
		 * @description Add paging to the item list on an issue or requirement page
		 */

		itemListOtherItems: function() {
			Roadmap.itemListOtherItems_size = 10;
			Roadmap.itemListOtherItems_page = 0;
			Roadmap.itemListOtherItems_count = 0;
			Roadmap.itemListOtherItems_pagecount = 0;

			$('#itemListOtherItems li').each(function(index, element) {
				if($(element).hasClass('selected')) {
					Roadmap.itemListOtherItems_page = Math.floor((index ) / Roadmap.itemListOtherItems_size) ;

				}
			});

			Roadmap.itemListOtherItemsPage();


		},

		itemListOtherItemsMove: function(direction) {
			Roadmap.itemListOtherItems_page += direction;
			if(Roadmap.itemListOtherItems_page < 0) {
				Roadmap.itemListOtherItems_page = 0;
			}
			if(Roadmap.itemListOtherItems_page  > Roadmap.itemListOtherItems_pagecount) {
				Roadmap.itemListOtherItems_page = itemListOtherItems_pagecount;
			}
			Roadmap.itemListOtherItemsPage();
		},

		/**
		 * @function
		 * @description Pages the list
		 */

		itemListOtherItemsPage: function() {
			var pageStart = Roadmap.itemListOtherItems_page * Roadmap.itemListOtherItems_size;
			var pageEnd = Roadmap.itemListOtherItems_page * Roadmap.itemListOtherItems_size + Roadmap.itemListOtherItems_size;

			$('#itemListOtherItems li').each(function(index, element) {
				if(index > Roadmap.itemListOtherItems_count) {
					Roadmap.itemListOtherItems_count = index;
				}

				if((index >= pageStart) && (index < pageEnd)) {
					$(element).show();
				} else {
					$(element).hide();
				}
			});

			if(Roadmap.itemListOtherItems_count > 0) {
				Roadmap.itemListOtherItems_pagecount = Math.floor((Roadmap.itemListOtherItems_count + 1) / Roadmap.itemListOtherItems_size) ;
			}
			var newHtml = ' <a onclick="return Roadmap.itemListOtherItemsMove(-1);">&#9664;</a> ';
			newHtml += 'Page ' + (Roadmap.itemListOtherItems_page + 1) + ' of ' + (parseInt(Roadmap.itemListOtherItems_pagecount) + 1).toString() ;
			newHtml += ' <a onclick="return Roadmap.itemListOtherItemsMove(1);">&#9654;</a> ';

			if(parseInt(Roadmap.itemListOtherItems_pagecount) > 0) {
				$('#itemListOtherItemsPage').html(newHtml);
			}
		},

		/**
 		 * @function
 		 * @description Show or hide the selected items in case we hit back
		 */

		itemCheckboxButtonBarInit: function() {
			var checkedItemsCount = $('#activeList input[type="checkbox"]:checked').length;
			if (checkedItemsCount > 0) {
				if ($('#selectedItems:visible').length == 0) {
					$.get('/roadmap/ledger/get_selected_items_bar', function(data) {
						$('#selectedItems').html(data);
						$('#selectedItems').fadeIn();
					});
				}
			}
		},

		/**
		 * @function
		 * @description Show or hide the menu bar at the bottom of the screen for selected items
		 *
		 */

		itemCheckboxMenuAppear: function(callback) {
			var checkedItemsCount = $('#activeList input[type="checkbox"]:checked').length;

			/**
			 * depending on whether we're showing or hiding the bar,
			 * call the function to populate the bar before or after.
			 *
			 * This stops flickering.
			 */
			if (checkedItemsCount == 0) {
				if ($('#selectedItems:visible').length == 1) {
					$('#selectedItems').fadeOut(callback);
				}
			} else {
				if (callback !== undefined) {
					callback();
				}
				if ($('#selectedItems:visible').length == 0) {
					$('#selectedItems').fadeIn();
				}
			}
		},

		/**
		 *	@function
		 *	@description Delete an item in a requirement objective.
		 *	@param {int} item_id The parent item ID
		 *	@param {int} checklistitem_id The checklist item ID
		 *	@param {String} itemType The type of the parent ID
		 *	@param {string} item The DOM element clicked on
		 *
		 */

		deleteObjective: function (item_id, checklistitem_id, itemType, item) {
			item.src = '/media/layout/images/indicator.white.gif';
			$.post('/roadmap/ledger/edit_checklist_item', {
				item_id: item_id,
				item_type: itemType,
				checklistitem_id: checklistitem_id,
				text: ''
			}, function (data) {
				$('li#checkList').html(data);
				Roadmap.hoverButtons($('#objectives'));
			});
		},

		/**
		 *	@function
		 */

		checklistClick: function (item_id, checklistitem_id, itemType, item) {
			var newTextBox = $('<input type="text" style="width:453px;" name="editChecklistItem" />');
			var elm = $(item);
			newTextBox.val(elm.text());
			var wrapper = $('<span/>');
			wrapper.append(newTextBox);
			var button = $('<button class="floatRight ui-state-default ui-corner-all dialog_link submit" type="button">Update</button>');
			wrapper.append(button);

			/**
			 *	@event
			 */

			button.click(function () {
				/*
				  Update server and list accordingly
				*/
				$.post('/roadmap/ledger/edit_checklist_item', {
					item_id: item_id,
					item_type: itemType,
					checklistitem_id: checklistitem_id,
					text: newTextBox.val()
				}, function (data) {
					$('li#checkList').html(data);
					Roadmap.hoverButtons($('#objectives'));
				});
			});

			/**
			 *	@event
			 */

			newTextBox.keydown(function (event) {
				if (event.keyCode == 13) {
					button.click();
				}
				if (event.keyCode == 27) {
					wrapper.replaceWith(elm);
				}
			});
			elm.replaceWith(wrapper);

			newTextBox.focus();
		},

		/**
		 *	@function
		 */

		addChecklistItem: function (item_id, file_uuid, itemText, itemType) {
			$.post('/roadmap/ledger/add_checklist_item', {
				item_id: item_id,
				item_text: itemText,
				item_type: itemType,
				file_uuid: file_uuid
			}, function (data) {
				$('#addStep').val('');
				$('#attachFileiFrameWrapper').html('<iframe id="attachFileiFrame" src="/roadmap/ledger/add_checklist_file?item_id=' + item_id + '&file_uuid=' + file_uuid + '" style="width: 400px; height: 3em;"></iframe>');
				$('li#checkList').html(data);
				Roadmap.hoverButtons($('#objectives'));
			});
			return false;
		},

		/**
		 *	@function
		 */

		slideInOut: function (item, link, showText, hideText) {
			if ($(item).is(':visible')) {
				$(item).parent().children('a').text(showText);
                $(item).fadeOut(150);
			} else {
				$(item).parent().children('a').text(hideText);
                $(item).fadeIn(150);
			}
		},

		/**
		 *	@function
		 */

		hideFlash: function () {
			$('#flash').hide();
		},

		/**
		 *	@function
		 */

		requestFollowUp: function (itemId, value, elm) {
			$.post('/roadmap/ledger/item_toggle_followup', {
				item_id: itemId,
				value: value
			}, function (data, textStatus) {
				if (data == 'success') {
					$(elm).html('Follow up requested');
				}
			});
		},

		/**
		 *	@function
		 */

		hoverButtons: function (container) {
			container.children('.hoverParent').each(function (index, element) {
				var jEl = $(element);

				jEl.hover(function () {
					$(this).find('.hoverButtons').show();
				}, function () {
					$(this).find('.hoverButtons').hide();
				});
			});
		},

		/**
		 *	@function
		 */

		setupSearch: function () {
			Roadmap.searchTrigger = null;
			Roadmap.searchPrevious = '';

			/**
			 *	@function
			 */

			$('#searchLauncher').click(function () {

				if ($('#searchWrapper').css('display') == 'block') {
					$('#searchWrapper').hide('slide', {
						direction: 'up'
					}, 150);
				} else {
					$('#searchWrapper').show('slide', {
						direction: 'up'
					}, 150, function () {
						$('#searchStart').focus();
					});
					$('#searchStart').val('');
					$('#searchResults').hide();
				}

				return false;
			});

			/**
			 *	@function
			 */

			$('#searchStart').keyup(function (key) {
				if (key.keyCode == 13 || key.keyCode == 38 || key.keyCode == 40) {
					return;
				}

				if ($('#searchStart').val().length > 2) {
					// Don't search if we've pressed buttons and nothing's changed
					if ($('#searchStart').val() != Roadmap.searchPrevious) {
						Roadmap.searchPrevious = $('#searchStart').val();

						// start spinner
						if (!$('#searchStart').hasClass('working')) {
							$('#searchStart').addClass('working');
						}

						// Only start searching after 1s
						if (Roadmap.searchTrigger) {
							window.clearTimeout(Roadmap.searchTrigger);
						}

						Roadmap.searchTrigger = window.setTimeout(function () {
							$.get('/search?q=' + escape($('#searchStart').val()), function (data) {
								Roadmap.searchIndex = -1;
								$('#searchResults').html(data);
								$('#searchResults').css('display', 'block');
								//$('#searchWrapper').css('display', 'block');
								Roadmap.searchSelector();

								if ($('#searchStart').hasClass('working')) {
									$('#searchStart').removeClass('working');
								}
							});
						}, 1000);
					}
				} else {
					$('#searchResults').html('<div/>');
					$('#searchResults').css('display', 'none');
				}
			});

			/**
			 *	@event
			 */

			$('#searchStart').keydown(function (key) {
				var refresh = false;

				//  Up arrow
				if (key.keyCode == 38) {
					Roadmap.searchIndex--;
					if (Roadmap.searchIndex < 0) {
						Roadmap.searchIndex = 0;
					}
					refresh = true;
				}

				//  Down arrow
				if (key.keyCode == 40) {
					Roadmap.searchIndex++;
					if (Roadmap.searchIndex > Roadmap.searchCount) {
						Roadmap.searchIndex = Roadmap.searchCount;
					}
					refresh = true;
				}

				//  Enter
				if (key.keyCode == 13) {
					if (Roadmap.searchLink) {
						window.location.href = Roadmap.searchLink;
					}
				}

				// ESC
				if (key.keyCode == 27) {
					$('#searchWrapper').hide('slide', {
						direction: 'up'
					}, 150);
				}


				if (refresh) {
					Roadmap.searchSelector();
				}
			});

			Roadmap.searchIndex = 0;
		},

		/**
		 *	@function
		 */

		searchSelector: function () {
			Roadmap.searchCount = -1;
			Roadmap.searchLink = null;

			$('#searchResults li').each(function (index, ele) {
				var jEle = $(ele);

				if (index == Roadmap.searchIndex) {
					if (!jEle.hasClass('selected')) {
						jEle.addClass('selected');
					}

					Roadmap.searchLink = jEle.find('a').attr('href');
				} else {
					if (jEle.hasClass('selected')) {
						jEle.removeClass('selected');
					}
				}
				Roadmap.searchCount = index;
			});
		},

		/**
		 *	@function
		 *	@description Attach handlers to tabs
		 */

		setupTabs: function () {
			return;
            var addressBarMark = '';
            if (window.location.href.indexOf('#') != -1) {
                addressBarMark = window.location.href.split('#')[1].replace('mark', '');
                $('#tabBar li a[href="#' + addressBarMark + '"]').parent().parent().addClass('selected');
            } else {
                $('#tabBar li .project').parent().addClass('selected');
            }
			$('#tabBar li a').each(function (index, ele) {
				if(ele.href.indexOf('#') != -1) {
					var tabLink = $(ele);
					tabLink.click(function (item) {
						var mark = ele.href.split('#')[1];
						if (item.target.href) {
							// highlight tab
							$('#tabBar li div').each(function (index, ele) {
								if ($(ele).hasClass('selected')) {
									$(ele).removeClass('selected');
								}
							});

							// hide other contents
							$('.tabContent').each(function (index, ele) {
								var jQueryEle = $(ele);
								jQueryEle.hide();
							});

							$('#' + item.target.href.split('#')[1]).show();

							$(item.target).parent().addClass('selected');

						}
						var oldLocation = window.location.href;
						if (oldLocation.indexOf('#') != -1) {
							oldLocation = oldLocation.split('#')[0];
						}
						window.location.href = oldLocation + '#mark' + mark;
						//return false;
					});
				}
			});

			//show selected tab
			$('#tabBar li').each(function (index, ele) {
				if ($(ele).hasClass('selected')) {
					$(ele).find('a').click();
				}
			});
		},

		/**
		 * 	@function
		 * 	@description Shameful hack to fix any layout issues
		 */

		patchLayout: function () {
			try {
				var min_height = Number($('#main-content').css('height').replace('px', ''));
				if ($('#line-divider').css('height').replace('px', '') > min_height) {
					min_height = $('#line-divider').css('height').replace('px', '');
				}
				$('#line-divider').css('height', min_height + 'px');
			} catch (e) {

			}
		},

		/**
		 *	@function
		 *	@description Setup any dropdowns with events
		 */

		setupDropdowns: function () {
			$('.dropdownSelect').each(function (index, ele) {

				/**
				 *	@private
				 *	@function
				 *	@description Mouse has left area. Start counting down ready to fade out
				 */

				function startCountdown() {
					if (ol.data('timeout') !== undefined) {
						window.clearTimeout(ol.data('timeout'));
					}

					ol.data('timeout', window.setTimeout(function () {
						ol.fadeOut();
					}, 1000));
				}

				/**
				 *	@private
				 *	@function
				 *	@description Mouse has entered list, clear timer so the list remains.
				 */

				function clearCountdown() {
					if (ol.data('timeout') !== undefined) {
						window.clearTimeout(ol.data('timeout'));
					}
				}

				var jEle = $(ele);
				var ol = $(ele).children('ol');
				var span = $(ele).children('span');
				var addDropdownArrow = $('<img src="/media/layout/icons/bullet_arrow_down.png" alt="Dropdown arrow" title="Change" />')
				span.append(addDropdownArrow);

				ol.css('left', '0');
				span.click(function (evt) {
					if (ol.css('display') == 'block') {
						ol.hide();
					} else {
						ol.show();
					}
					return false;
				});

				span.mousemove(function (evt) {
					clearCountdown();
				});

				ol.mousemove(function (evt) {
					clearCountdown();
				});

				span.mouseout(function (evt) {
					startCountdown();
				});

				ol.mouseout(function (evt) {
					startCountdown();
				});

				ol.children('li').each(function (index, ele) {
					$(ele).click(function () {
						var locationChange = window.location.href;
						var oldLocation = span.text();
						var newLocation = $(ele).text();
						locationChange = locationChange.replace(oldLocation, newLocation);
						window.location.href = locationChange;
					});
				});
			});
		},

		/**
		 *	@function
		 */

		setupBreadCrumb: function () {
			return;
            var screenWidth = $(window).width();

            function slideIn() {
                $('#toolbox').css({ left: screenWidth, display: 'block' });
                $('#location').animate( { left: '-' + screenWidth }, 500, function() {

                });
                $('#toolbox').animate( { left: '0' }, 500, function() {

                });
            }
            function slideOut() {
                $('#toolbox').css({ left: screenWidth, display: 'block' });
                $('#location').animate( { left: '0' }, 500, function() {

                });
                $('#toolbox').animate( { left:  screenWidth }, 500, function() {

                });
            }

            function fadeItemsOut() {
                toolbox.fadeOut(100, function () {
                    $('#location').fadeIn(50);
                });
            }

            function fadeItemsIn() {
                $('#location').fadeOut(100, function () {
					$('#toolbox').fadeIn(100, function () {

					});
				});
            }

			$('#addItemLink').click(function () {
                fadeItemsIn();
			});

            function addNewItem() {
                var location = $('#location');
                var width = $(window).width();
            }

			var toolbox = $('#toolbox');
			var breadCrumb = $('#breadCrumb');

            /*
            Mouse has left area. Start counting down ready to fade out
            */
			function startCountdown() {
				if (toolbox.data('timeout') !== undefined) {
					window.clearTimeout(toolbox.data('timeout'));
				}

				toolbox.data('timeout', window.setTimeout(function () {
                    fadeItemsOut();
				}, 1000));
			}

            /*
            Mouse has entered list, clear timer so the list remains.
            */

			function clearCountdown() {
				if (toolbox.data('timeout') !== undefined) {
					window.clearTimeout(toolbox.data('timeout'));
				}
			}

			breadCrumb.mouseenter(function (evt) {
				clearCountdown();
			});

			breadCrumb.mousemove(function (evt) {
				clearCountdown();
			});

			breadCrumb.mouseout(function (evt) {
				startCountdown();
			});
		},

        /**
		 *	@function
		 *
		 *	@description Insta Filter. Put the class of .instaFilter on the container you wish to add a filter to.
		 *	Add an input box with class of .instaFilterInput
		 *	For each row you want to filter, add .instaFilterThis
		 */

        setupInstaFilter: function(startElement) {
			var findElements = null;
			if (typeof(startElement) == 'undefined') {
				findElements = $('.instaFilter');
			} else {
				findElements = startElement.find('.instaFilter');
			}

            findElements.each(function(ifIndex, instaFilter) {
                var instaObject = $(instaFilter);
                var instaFilterInput = $(instaFilter).find('.instaFilterInput');
                instaFilterInput.val('');

                instaObject.keydown(function(key) {
                    var useArrows = false;
                   /*
                     Escape clears the box
                    */
                    if (key.keyCode == 27) {
                        instaFilterInput.val('');
                    }

                    if(useArrows) {
                        //  Up arrow
                        if (key.keyCode == 38) {
                            var checkForSelected = instaObject.find('.instaFilterSelected');

                            // if nothing selected
                            if(checkForSelected.length == 0) {
                                // select the first one
                                var getThis = instaObject.find('.instaFilterThis')[0];
                                $(getThis).addClass('instaFilterSelected');
                            } else {
                                var nextItem = instaObject.find('.instaFilterThis.instaFilterSelected');
                                nextItem.prev().addClass('instaFilterSelected');
                                checkForSelected.removeClass('instaFilterSelected');
                            }
                        }

                        //  Down arrow
                        if (key.keyCode == 40) {
                            var checkForSelected = instaObject.find('.instaFilterSelected');

                            // if nothing selected
                            if(checkForSelected.length == 0) {
                                // select the first one
                                var getThis = instaObject.find('.instaFilterThis')[0];
                                $(getThis).addClass('instaFilterSelected');
                            } else {
                                var nextItem = instaObject.find('.instaFilterThis.instaFilterSelected');
                                nextItem.next().addClass('instaFilterSelected');
                                checkForSelected.removeClass('instaFilterSelected');
                            }
                        }
                    }

                    //  Enter
                    if (key.keyCode == 13) {
                        var selectedItem = instaObject.find('.instaFilterThis.instaFilterSelected');
                        if(selectedItem.length != 0) {
                            var link = selectedItem.find('a');
                            if(link != 0) {
                                link[0].click();
                                selectedItem.removeClass('instaFilterSelected');
                                return;
                            }
                        }
                    }

                });

                instaFilterInput.keyup(function(key) {
                   var filterOn = instaFilterInput.val().toLowerCase();
                   var splitList = filterOn.split(' ');

                   $(instaFilter).find('.instaFilterThis').each(function(index, element) {
                        var jElement = $(element);

                        if( filterOn != '') {
                            var show = true;

                            for(loopItem in splitList) {
                               if(jElement.html().toLowerCase().indexOf(splitList[loopItem]) == -1) {
                                    show = false;
                               }
                            }

                            if(show) {
                                jElement.show();
                            } else {
                                jElement.hide();
                            }
                        } else {
                            jElement.show();
                        }
                   });

                   return false;
                });
            });
        },

		/**
		 * @function
		 */

        itemsExpandLocation: function(href, show, locationId, linkElement) {
          $.get(href,function(data) {
            if(show) {
                $('#location' + locationId).show();
                $(linkElement).parent().parent().find('.showButton').hide();
                $(linkElement).parent().parent().find('.hideButton').show();
            } else {
                $('#location' + locationId).hide();
                $(linkElement).parent().parent().find('.showButton').show();
                $(linkElement).parent().parent().find('.hideButton').hide();
            }
          });
          return false;
        },

		/**
		 *	@function
		 */

		addLinkedItemPopup: function(id) {
			var popup = $('<div id="addLinkedItemPopup" ></div>');
			$('body').append(popup);
			popup.center();
			$.get('/roadmap/ledger/add_linked_item_popup?id=' + id, function(data) {
				var parsedTemplate = $(data);
				popup.append(parsedTemplate);
				Roadmap.setupInstaFilter(popup);
				parsedTemplate.find('#addLinkedItemsTabs li:first').addClass('selected');

				parsedTemplate.find('#addLinkedItemsTabs li a').each(function(index, element) {
					$(element).click(function(evt) {
						parsedTemplate.find('#addLinkedItemsTabs li').each(function(hIndex, hElement) {
							if($(hElement).hasClass('selected')) {
								$(hElement).removeClass('selected');
							}
						});

						$(element).parent().addClass('selected');

						var searchId = $(element).parent().attr('id');
						parsedTemplate.find('.tab').each(function(tabIndex, tabElement) {
							if($(tabElement).hasClass('tab_' + searchId)) {
								$(tabElement).css( { 'display' : 'block '});
							} else {
								$(tabElement).css( { 'display' : 'none '});
							}
						});

						return false;
					});
				});

				// show first tab
				parsedTemplate.find('.tab:first').show();
				parsedTemplate.find('.tab:first').addClass('selected');
			});

			function fadeItemsOut() {
				popup.fadeOut(500, function() {
					popup.remove();
				});
			}
			/*
            Mouse has left area. Start counting down ready to fade out
            */
			function startCountdown() {
				if (popup.data('timeout') !== undefined) {
					window.clearTimeout(popup.data('timeout'));
				}

				popup.data('timeout', window.setTimeout(function () {
                    fadeItemsOut();
				}, 1000));
			}

            /*
            Mouse has entered list, clear timer so the list remains.
            */

			function clearCountdown() {
				if (popup.data('timeout') !== undefined) {
					window.clearTimeout(popup.data('timeout'));
				}
			}

			popup.mouseenter(function (evt) {
				clearCountdown();
			});

			popup.mousemove(function (evt) {
				clearCountdown();
			});

			popup.mouseout(function (evt) {
				startCountdown();
			});

			return false;
		},

		/**
		 *	@function
		 */

		toolboxEvents: function() {
			$('#toolbox').html('<span class="linkButton" style=" color:#FB9E4A; padding-right: 0px;"></span>' + $('#toolbox').html());


			$('.linkButton').each(function(spanIndex, spanElement) {
				var jElement = $(spanElement);

				jElement.mouseover(function(data_send) {
					if(!jElement.hasClass('hover')) {
						jElement.addClass('hover');
					}
				});
				jElement.mouseout(function(data_send) {
					if(jElement.hasClass('hover')) {
						jElement.removeClass('hover');
					}
				});
				jElement.click(function(data_send) {
					window.location.href=$(data_send.currentTarget).find('a').attr('href');
				});
			});

		},

		/**
		 * @function
		 * @description Show/hide the collapser
		 */

		updatedItemsCollapse: function() {
			var link = $('#unseenNotification');
			var box = $('#latestUpdatesCollapse');

			link.click(function() {

				if (box.is(':visible')) {
					box.hide('slide', {
						direction: 'up'
					}, 150);
				} else {
					box.show('slide', {
						direction: 'up'
					}, 150);
				}

				return false;
			});
		},

		/**
		 *	@function
		 */

		Initialise: function () {
            Roadmap.setupInstaFilter();
			Roadmap.hoverButtons($('#comments'));
			Roadmap.hoverButtons($('#objectives'));
			Roadmap.checkFeed();
			//    	Chat.initialiseChat();
			Roadmap.activeMenu();
			Roadmap.hideFlash();
			Roadmap.setupTabs();
			Roadmap.setupSearch();
			Roadmap.popupMenuInitialise();
			Roadmap.setupDropdowns();
			Roadmap.setupBreadCrumb();
			Roadmap.activeItemsHover();

			Roadmap.patchLayout();
			Roadmap.toolboxEvents();
			Roadmap.itemCheckboxButtonBarInit();
			Roadmap.itemListOtherItems();
			Roadmap.grouping.initialise();
			Roadmap.reminders.initialise();
			Roadmap.navigationSearch.initialise();
			Roadmap.updatedItemsCollapse();

			$('#djDebug').show();
			$('#djDebugToolbar').show();
			tagComplete();

		}
	}
})();















var loader = [];
var main = null;
var closingMenu = null;

function tagComplete() {
	$(function () {

		function split(val) {
			return val.split(/,\s*/);
		}

		function extractLast(term) {
			return split(term).pop();
		}

		if($("#id_tags").length > 0) {
			$("#id_tags").autocomplete({
				minLength: 0,
				source: function (request, response) {
					// delegate back to autocomplete, but extract the last term
					response($.ui.autocomplete.filter(availableTags, extractLast(request.term)));
				},
				focus: function () {
					// prevent value inserted on focus
					return false;
				},
				select: function (event, ui) {
					var terms = split(this.value);
					// remove the current input
					terms.pop();
					// add the selected item
					strip_name = ui.item.value;
					strip_name = strip_name.split(' ');
					item_value = ui.item.value;
					if (strip_name.length > 0) {
						item_value = strip_name[1];
					}
					terms.push(strip_name);
					// add placeholder to get the comma-and-space at the end
					terms.push("");
					this.value = terms.join(", ");
					return false;
				}
			});

		}

		if($("#tags").length > 0) {
			$("#tags").autocomplete({
				minLength: 0,
				source: function (request, response) {
					// delegate back to autocomplete, but extract the last term
					response($.ui.autocomplete.filter(availableTags, extractLast(request.term)));
				},
				focus: function () {
					// prevent value inserted on focus
					return false;
				},
				select: function (event, ui) {
					var terms = split(this.value);
					// remove the current input
					terms.pop();
					// add the selected item
					strip_name = ui.item.value;
					strip_name = strip_name.split(' ');
					item_value = ui.item.value;
					if (strip_name.length > 0) {
						item_value = strip_name[1];
					}
					terms.push(strip_name);
					// add placeholder to get the comma-and-space at the end
					terms.push("");
					this.value = terms.join(", ");
					return false;
				}
			});
		}
	});
}

//@class
//@name initChat
function initChat() {
	Chat.initialiseChat(Properties);
}

Roadmap.addLoader(Roadmap.Initialise); /* Roadmap.addLoader(initChat); */

$().ready(function () {

	for (var i = 0; i < Roadmap.loader.length; i++) {
		Roadmap.loader[i]();
	}
});