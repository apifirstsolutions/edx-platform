$(document).ready(function() {
    $('.js-select-category').on('click', function(ev) {
        ev.stopPropagation();
        var value = $(ev.currentTarget).data('category-id');
        loadFilter('category', value, ['subcategory']);
    });

    $('.js-select-subcategory').on('click', function(ev) {
        ev.stopPropagation();
        var value = $(ev.currentTarget).data('subcategory-id');
        loadFilter('subcategory', value, ['category']);
    });

//    $('.search-btn').on('click', function (ev) {
//      ev.stopPropagation();
//      var value = $('.js-search-input').val();
//      loadFilter('search', value, []);
//    });

    $('.js-reset-category').on('click', function(ev) {
        ev.stopPropagation();
        loadFilter('', '', ['category', 'subcategory']);
    });

    $('.js-select-difficulty-level').on('change', function(ev) {
        loadFilter('difficulty_level', this.value, [])
    })

    $('.js-select-mode').on('change', function(ev) {
        loadFilter('mode', this.value, [])
    })

    $('.js-select-sort').on('change', function(ev) {
        loadFilter('sort', this.value, [])
    })

    function loadFilter(name, value, deleteNames) {
        let params = new URLSearchParams(window.location.search);
        console.log("deleteNames",deleteNames)
        for (let deleteName of deleteNames) {
            params.delete(deleteName);
        }
        params.set(name, value);
        console.log("$('#search').val()", $('#search').val(),params.toString())
        window.location.search = params.toString()
//        !$('#search').val()?window.location.search = params.toString():null;
    }
});
