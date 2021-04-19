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
        for (let deleteName of deleteNames) {
            params.delete(deleteName);
        }
        params.set(name, value);
        window.location.search = params.toString();
    }
});
