var viewedSlider_bundled = $("#bundled_courses_ul");

function show_bundled_courses(target) {

    var form = new FormData();

    var settings = {
        "url": target,
        "method": "GET",
        "headers": {
            'X-CSRFToken': $('#web_csrf_token').val()
        },
        "processData": false,

        "contentType": false,
    };

    $("#bundled_courses_loader").css("display", "");

    $.ajax(settings).done(function(response) {
        $('#bundled_courses_ul').owlCarousel('destroy');
        $("#bundled_courses_ul").html('');
        $("#bundled_courses_loader").css("display", "None")
        
        $('#heading_recommended_courses').css('display', '');
        $('.courses-listing').empty();
    
        if(response["next"] != null){
            $("#bundled_next_btn").css("display","");
            bundled_next_url = target + '?page=' + response["next"].toString();
        } else {
            $("#bundled_next_btn").css("display","None")
        }

        if(response["previous"] != null){
            $("#bundled_prev_btn").css("display","");
            bundled_prev_url = target + '?page=' + response["previous"].toString();
        } else {
            $("#bundled_prev_btn").css("display","None")
        }

        plans = response['results'];

        console.log('plans', plans)
        
        for (var i = 0; i < plans.length; i++) {
            var plan_card = `<li class="card-slider-card-items owl-item">
            <article class="card-slider-course">
                <a href="/plan/`+plans[i]['slug']+`/">
                    <header class="card-slider-card-img-cont">
                    <div class="card-slider-card-cover-img">
                        <img src="` + plans[i]['image_url'] + `" alt="` + plans[i]['name'] + `">
                        <div class="card-slider-card-learn-more-btn" aria-hidden="true">LEARN MORE</div>
                    </div>
                    </header>
                    <div class="card-slider-card-course-info" aria-hidden="true">
                    <h2 class="crd-sldr-course-info ">
                        <span class="crd-sldr-course-info-org">&nbsp;</span>
                        <span class="crd-sldr-course-info-title">` + plans[i]['name'] + `</span>
                        <p class="crd-sldr-course-info-label">Courses:<span class="course-difficulty_level">` + plans[i]['course_count'] + `</span></p>
                        
                        <div class="crd-sldr-course-info-price fl">
                            <ul>
                                <li>Price: <span class="main_price">By subscription</span></li>
                                `;
                                
                                prices = '';
                                if (plans[i]['price_month']) {
                                    prices += `<li><p class="crd-sldr-course-info-label">Monthly:<span class="course-difficulty_level">S$` + plans[i]['price_month'] + `</span></p></li>`;
                                }
                                if (plans[i]['price_year']) {
                                    prices += `<li><p class="crd-sldr-course-info-label">Yearly:<span class="course-difficulty_level">S$` + plans[i]['price_year'] + `</span></p></li>`;
                                }
                                if (plans[i]['price_onetime']) {
                                    prices += `<li><p class="crd-sldr-course-info-label">Onetime:<span class="course-difficulty_level">S$` + plans[i]['price_onetime'] + `</span></p></li>`;
                                }

                                plan_card += prices +`
                            </ul>
                        </div>
                    </h2>
                    <div class="crd-sldr-course-info-date" aria-hidden="true">Available until: ` + plans[i]['valid_until_formatted'] + `</div>
                    </div>
                </a>
            </article>
            </li>`;

            $("#bundled_courses_ul").append(plan_card)
        }

        var viewedSlider_bundled = $('#bundled_courses_ul');
        viewedSlider_bundled.owlCarousel({
            loop: false,
            margin: 20,
            autoplay: false,
            autoplayTimeout: 6000,
            dots: false,
            items: 20,
            slideBy: 4,
            responsive:
            {
                0:{items:1},
                768:{items:2},
                991:{items:4}
            }
        });
    });
}

$(document).ready(function() {
    
    
    // Bundled Courses Slider Button
    // From here
    if ($('#bundled_prev_btn').length) {
        var prev = $('#bundled_prev_btn');
        prev.on('click', function() {
            viewedSlider_bundled.trigger('prev.owl.carousel');
            show_bundled_courses(free_prev_url);
            $('#bundled_prev_btn').show();
        });
    }
    if ($('#bundled_next_btn').length) {
        var next = $('#bundled_next_btn');
        next.on('click', function() {
            viewedSlider_bundled.trigger('next.owl.carousel');
            show_bundled_courses(free_next_url);
            $('#bundled_next_btn').show();
        });
    }
    // till here

    show_bundled_courses(window.location.protocol + '//' + window.location.host + "/api/subscriptions/featured-plans/");
        


});

