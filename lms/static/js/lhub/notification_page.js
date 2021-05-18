$(document).ready(function() {
  'use strict';

  $('.js-mark-read-status').on('click', function(ev) {
    ev.preventDefault();
    var $ev = $(ev.currentTarget);
    var url = $ev.data('url');
    var isRead = $ev.data('is-read');
    $.ajax({
        url: url,
        type: 'PUT',
        data: {is_read: !isRead},
        success: function (result) {
          if (!isRead) {
            $ev.parents('.js-item-notification').removeClass('new-notification');
            $ev.children('.js-mark-as-read').addClass('hidden');
            $ev.children('.js-mark-as-unread').removeClass('hidden');
          }
          else {
            $ev.parents('.js-item-notification').addClass('new-notification');
            $ev.children('.js-mark-as-read').removeClass('hidden');
            $ev.children('.js-mark-as-unread').addClass('hidden');
          }
          $ev.data('is-read', !isRead);
        },
    });
  });

  $('.js-delete-notification').on('click', function(ev) {
    ev.preventDefault();
    var $ev = $(ev.currentTarget);
    var url = $ev.data('url');
    $.ajax({
        url: url,
        type: 'DELETE',
    });
    $ev.parents('.js-item-notification').remove();
  });

  $('.js-mark-all-as-read').on('click', function(ev) {
    ev.preventDefault();
    let $ev = $(ev.currentTarget);
    let url = $ev.data('url');
    let checkedInputs = [];

    $.each($("input[name='notification']:checked"), function(){
      checkedInputs.push($(this).data('id'));
    });

    $.ajax({
      url: url,
      type: 'POST',
      contentType: 'application/json; charset=utf-8',
      dataType: 'json',
      data: JSON.stringify({
        ids: checkedInputs
      }),
      success: function () {
        $.each(checkedInputs, function(){
          let checkbox = $(`#notification-${this}`);
          checkbox.removeAttr('checked');
          checkbox.parents('.js-item-notification').removeClass('new-notification');
          let actions = checkbox.parents('.js-item-notification').find('.notification-list-actions .js-mark-read-status');
          actions.find('.js-mark-as-read').addClass('hidden');
          actions.find('.js-mark-as-unread').removeClass('hidden');
        });
      }
    })
  });

  $('.js-mark-all-as-unread').on('click', function(ev) {
    ev.preventDefault();
    let $ev = $(ev.currentTarget);
    let url = $ev.data('url');
    let checkedInputs = [];

    $.each($("input[name='notification']:checked"), function(){
      checkedInputs.push($(this).data('id'));
    });

    $.ajax({
      url: url,
      type: 'POST',
      contentType: 'application/json; charset=utf-8',
      dataType: 'json',
      data: JSON.stringify({
        ids: checkedInputs
      }),
      success: function () {
        $.each(checkedInputs, function() {
          let checkbox = $(`#notification-${this}`);
          checkbox.removeAttr('checked');
          checkbox.parents('.js-item-notification').addClass('new-notification');
          let actions = checkbox.parents('.js-item-notification').find('.notification-list-actions .js-mark-read-status');
          actions.find('.js-mark-as-read').removeClass('hidden');
          actions.find('.js-mark-as-unread').addClass('hidden');
        });
      }
    })
  });

  $('.js-delete-all').on('click', function(ev) {
    ev.preventDefault();
    let $ev = $(ev.currentTarget);
    let url = $ev.data('url');
    let checkedInputs = [];

    $.each($("input[name='notification']:checked"), function(){
      checkedInputs.push($(this).data('id'));
    });

    $.ajax({
      url: url,
      type: 'POST',
      contentType: 'application/json; charset=utf-8',
      dataType: 'json',
      data: JSON.stringify({
        ids: checkedInputs
      }),
      success: function () {
        $.each(checkedInputs, function() {
          $(`#notification-${this}`).parents('.js-item-notification').remove();
        });
      }
    })
  });
});
