var popular_next_url;
var popular_prev_url;
var free_next_url;
var free_prev_url;
var top_next_url ;
var top_prev_url;
var recommended_next_url;
var recommended_prev_url;
var viewedSlider_pop = $('#most_popular_ul');
var viewedSlider_rec = $("#recommended_courses_ul");
var viewedSlider_free = $("#free_courses_ul");
var viewedSlider_bundled = $("#bundled_courses_ul");
var viewedSlider_top = $("#top_rated_ul");


function show_most_popular_courses(target) {

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
    $("#most_popular_loader").css("display", "");

    $.ajax(settings).done(function(response) {
    $('#most_popular_ul').owlCarousel('destroy');
    $("#most_popular_ul").html('');
        $("#most_popular_loader").css("display", "None");
        console.log(response);
        if (response['status_code'] == 200) {
            $('#heading_recommended_courses').css('display', '')
            $('.courses-listing').empty()
        pagination_popular_url = response['result']['pagination']["next"];
        if( pagination_popular_url != null){
            $("#popular_next_btn").css("display","");
            popular_next_url = pagination_popular_url;
        }
        else {
            $("#popular_next_btn").css("display","None")
        }
        if(response['result']['pagination']["previous"] != null){
            $("#popular_prev_btn").css("display","");
            popular_prev_url = response['result']['pagination']["previous"];
        }
        else {
            $("#popular_prev_btn").css("display","None");
        }
            for (var i = 0; i < response['result']['results'].length; i++) {
                course_id = response['result']['results'][i]['course_number'];
                course_org = response['result']['results'][i]['organization'];
                course_code = response['result']['results'][i]['id'];
                course_name = response['result']['results'][i]['name'];
                course_image = response['result']['results'][i]["media"]['image']["raw"];
                course_difficulty_level = response['result']['results'][i]['difficulty_level'];
                course_enrollments_count = response['result']['results'][i]['enrollments_count'];
                course_ratings = response['result']['results'][i]['ratings'];
                course_ratings = course_ratings !== null ? course_ratings : "None";
                course_comments_count = response['result']['results'][i]['comments_count'];

                course_start = response['result']['results'][i]['start_date'];
                course_discount_applicable = response['result']['results'][i]['discount_applicable'];
                course_price = response['result']['results'][i]['modes'][0]['price'];
                course_discount_type = response['result']['results'][i]['discount_type'];
                course_discounted_price = response['result']['results'][i]['discounted_price'];
                course_discount_percentage = response['result']['results'][i]['discount_percentage'];

                var course = `<li class="card-slider-card-items owl-item">
               <article class="card-slider-course">
                  <a href="/courses/`+course_code+`/about">
                     <header class="card-slider-card-img-cont">
                        <div class="card-slider-card-cover-img">
                           <img src="` + course_image + `" alt="` + course_name + `">
                           <div class="card-slider-card-learn-more-btn" aria-hidden="true">LEARN MORE</div>
                        </div>
                     </header>
                     <div class="card-slider-card-course-info" aria-hidden="true">
                        <h2 class="crd-sldr-course-info ">
                           <span class="crd-sldr-course-info-org">` + course_org + `</span>
                           <span class="crd-sldr-course-info-code fl">` + course_id + `</span>
                           <span class="crd-sldr-course-info-title">` + course_name + `</span>
                           <p class="crd-sldr-course-info-label">Difficulty Level:<span class="course-difficulty_level">` + course_difficulty_level + `</span></p>
                           <p class="crd-sldr-course-info-label">Enrollment Count:<span class="course-enrollments_count">` + course_enrollments_count + `</span></p>
                           <p class="crd-sldr-course-info-label">Rating:<span class="course-ratings">` + course_ratings + `</span></p>
                           <p class="crd-sldr-course-info-label">Comments Count:<span class="course-comments_count">` + course_comments_count + `</span></p>

                           <div class="crd-sldr-course-info-price fl">
                              <ul>`
                                 if (course_discount_applicable == true)
                                {
                                    if (course_discount_type == 'Percentage'){
                                 course +=`<li>Discount Percentage: <span class="main_price-percentage">`+course_discount_percentage+`%</span></li>`
                                 }
                                 else {
                                    course +=`<li>Discount: <span class="main_price-percentage">S$`+course_discount_percentage+`</span></li>`
                                 }

                                 course +=`<li>Price: <span class="crd-sldr-course-info-main-price main_price_cut">  ` + course_price + ` </span></li>
                                 <li>Discounted Price: <span class="main_price">S$`+course_discounted_price+`</span></li>`
                                }
                                else if (course_discount_applicable == false && course_price > 0 )
                                {

                                    course +=`<li>Price: <span class="main_price">S$`+course_price+`</span></li>`
                                }
                                else
                                {
                                    course +=`<li>Price: <span class="main_price">Free</span></li>`
                                }

                                course +=`

                              </ul>
                            </div>`

                           available_vouchers = response['result']['results'][i]['available_vouchers'];
                           if (available_vouchers.length > 0)
                                {
                                   course+=`<div class="coupon_details">`
                                  for (var j=0; j < available_vouchers.length; j++)
                                  {
                                        if (available_vouchers[j]["discount_type"] == 'Absolute')
                                        {

                                           course+= `<p><span class="coupen_code_value"><i class="fa fa-check"></i>`+ available_vouchers[j]["code"] +` -S$` + available_vouchers[j]["discount_value"]+`</span></p>`
                                        }
                                        else
                                        {

                                         course+=   `<p><span class="coupen_code_value"><i class="fa fa-check"></i>` +available_vouchers[j]["code"]+ ` -`+available_vouchers[j]["discount_value"]+`%</span></p>`
                                        }
                                    }
                            course+=`</div>`
                        }

                        course+=`</h2>
                        <div class="crd-sldr-course-info-date" aria-hidden="true" data-format="shortDate" data-datetime="2013-02-05T05:00:00+0000" data-language="en" data-string="Starts: {date}">Starts: ` + course_start + `</div>
                     </div>
                  </a>
               </article>
            </li>`;



                $("#most_popular_ul").append(course);

            }
        var viewedSlider_pop = $('#most_popular_ul');
        viewedSlider_pop.owlCarousel({
        loop: false,
        margin: 20,
        autoplay: false,
        autoplayTimeout: 6000,
        dots: false,
        items: 4,
        slideBy: 4,
        responsive:
        {
        0:{items:1},
        768:{items:2},
        991:{items:4}
        }
        });


        }
    });

}


function show_free_courses(target) {

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

    $("#free_courses_loader").css("display", "");
    $.ajax(settings).done(function(response) {
    $('#free_courses_ul').owlCarousel('destroy');
    $("#free_courses_ul").html('');
        $("#free_courses_loader").css("display", "None")
        console.log(response);
        if (response['status_code'] == 200) {
            $('#heading_recommended_courses').css('display', '');
            $('.courses-listing').empty();
        pagination_free_url = response['result']['pagination']["next"];
        if( pagination_free_url != null){
            $("#free_next_btn").css("display","");
            free_next_url = pagination_free_url;
        }
        else {
            $("#free_next_btn").css("display","None")
        }
           if(response['result']['pagination']["previous"] != null){
            $("#free_prev_btn").css("display","");
            free_prev_url = response['result']['pagination']["previous"];
        }
        else {
            $("#free_prev_btn").css("display","None")
        }
            for (var i = 0; i < response['result']['results'].length; i++) {
                course_id = response['result']['results'][i]['course_number'];
                course_org = response['result']['results'][i]['organization'];
                course_code = response['result']['results'][i]['id'];
                course_name = response['result']['results'][i]['name'];
                course_image = response['result']['results'][i]["media"]['image']["raw"];
                course_difficulty_level = response['result']['results'][i]['difficulty_level'];
                course_enrollments_count = response['result']['results'][i]['enrollments_count'];
                course_ratings = response['result']['results'][i]['ratings'];
                course_ratings = course_ratings !== null ? course_ratings : "None";
                course_comments_count = response['result']['results'][i]['comments_count'];
                course_discount_type = response['result']['results'][i]['discount_type'];

                course_start = response['result']['results'][i]['start_date'];
                course_discount_applicable = response['result']['results'][i]['discount_applicable'];
                course_price = response['result']['results'][i]['modes'][0]['price'];

                course_discounted_price = response['result']['results'][i]['discounted_price'];
                course_discount_percentage = response['result']['results'][i]['discount_percentage'];

                var course = `<li class="card-slider-card-items owl-item">
               <article class="card-slider-course">
                  <a href="/courses/`+course_code+`/about">
                     <header class="card-slider-card-img-cont">
                        <div class="card-slider-card-cover-img">
                           <img src="` + course_image + `" alt="` + course_name + `">
                           <div class="card-slider-card-learn-more-btn" aria-hidden="true">LEARN MORE</div>
                        </div>
                     </header>
                     <div class="card-slider-card-course-info" aria-hidden="true">
                        <h2 class="crd-sldr-course-info ">
                           <span class="crd-sldr-course-info-org">` + course_org + `</span>
                           <span class="crd-sldr-course-info-code fl">` + course_id + `</span>
                           <span class="crd-sldr-course-info-title">` + course_name + `</span>
                           <p class="crd-sldr-course-info-label">Difficulty Level:<span class="course-difficulty_level">` + course_difficulty_level + `</span></p>
                           <p class="crd-sldr-course-info-label">Enrollment Count:<span class="course-enrollments_count">` + course_enrollments_count + `</span></p>
                           <p class="crd-sldr-course-info-label">Rating:<span class="course-ratings">` + course_ratings + `</span></p>
                           <p class="crd-sldr-course-info-label">Comments Count:<span class="course-comments_count">` + course_comments_count + `</span></p>

                           <div class="crd-sldr-course-info-price fl">
                              <ul>`
                                  if (course_discount_applicable == true)
                                {
                                    if (course_discount_type == 'Percentage'){
                                 course +=`<li>Discount Percentage: <span class="main_price-percentage">`+course_discount_percentage+`%</span></li>`
                                 }
                                 else {
                                    course +=`<li>Discount: <span class="main_price-percentage">S$`+course_discount_percentage+`</span></li>`
                                 }

                                 course +=`<li>Price: <span class="crd-sldr-course-info-main-price main_price_cut">  ` + course_price + ` </span></li>
                                 <li>Discounted Price: <span class="main_price">S$`+course_discounted_price+`</span></li>`
                                }
                                else if (course_discount_applicable == false && course_price > 0 )
                                {

                                    course +=`<li>Price: <span class="main_price">S$`+course_price+`</span></li>`
                                }
                                else
                                {
                                    course +=`<li>Price: <span class="main_price">Free</span></li>`
                                }

                                course +=`

                              </ul>
                           </div>`

                           available_vouchers = response['result']['results'][i]['available_vouchers'];
                           if (available_vouchers.length > 0)
                                {
                                   course+=`<div class="coupon_details">`
                                  for (var j=0; j < available_vouchers.length; j++)
                                  {
                                        if (available_vouchers[j]["discount_type"] == 'Absolute')
                                        {

                                           course+= `<p><span class="coupen_code_value"><i class="fa fa-check"></i>`+ available_vouchers[j]["code"] +` -S$` + available_vouchers[j]["discount_value"]+`</span></p>`
                                        }
                                        else
                                        {

                                         course+=   `<p><span class="coupen_code_value"><i class="fa fa-check"></i>` +available_vouchers[j]["code"]+ ` -`+available_vouchers[j]["discount_value"]+`%</span></p>`
                                        }
                                    }
                            course+=`</div>`
                        }

                        course+=`</h2>
                        <div class="crd-sldr-course-info-date" aria-hidden="true" data-format="shortDate" data-datetime="2013-02-05T05:00:00+0000" data-language="en" data-string="Starts: {date}">Starts: ` + course_start + `</div>
                     </div>
                  </a>
               </article>
            </li>`;



                $("#free_courses_ul").append(course)

            }

        var viewedSlider_free = $('#free_courses_ul');
        viewedSlider_free.owlCarousel({
        loop: false,
        margin: 20,
        autoplay: false,
        autoplayTimeout: 6000,
        dots: false,
        items: 4,
        slideBy: 4,
        responsive:
        {
        0:{items:1},
        768:{items:2},
        991:{items:4}
        }
        });
        }
    });

}

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
            items: 4,
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

function show_top_rated_courses(top_rated) {

    var form = new FormData();
    var settings = {
        "url": top_rated,
        "method": "GET",
        "headers": {
            'X-CSRFToken': $('#web_csrf_token').val()
        },
        "processData": false,

        "contentType": false,
    };

    $("#top_rated_loader").css("display", "");
    $.ajax(settings).done(function(response) {
    $('#top_rated_ul').owlCarousel('destroy');
    $("#top_rated_ul").html('');
        $("#top_rated_loader").css("display", "None")
        console.log(response);
        if (response['status_code'] == 200) {
            $('.courses-listing').empty();
        pagination_top_url = response['result']['pagination']["next"];
        if( pagination_top_url != null){
            $("#top_next_btn").css("display","");
            top_next_url = pagination_top_url;
        }
        else {
            $("#top_next_btn").css("display","None");
        }
        if(response['result']['pagination']["previous"] != null){
            $("#top_prev_btn").css("display","");
            top_prev_url = response['result']['pagination']["previous"];
        }
        else {
            $("#top_prev_btn").css("display","None");
        }

            for (var i = 0; i < response['result']['results'].length; i++) {
                course_id = response['result']['results'][i]['course_number'];
                course_org = response['result']['results'][i]['organization'];
                course_code = response['result']['results'][i]["id"];
                course_name = response['result']['results'][i]['name'];
                course_image = response['result']['results'][i]["media"]['image']["raw"];
                course_difficulty_level = response['result']['results'][i]['difficulty_level'];
                course_enrollments_count = response['result']['results'][i]['enrollments_count'];
                course_ratings = response['result']['results'][i]['ratings'];
                course_ratings = course_ratings !== null ? course_ratings : "None";
                course_comments_count = response['result']['results'][i]['comments_count'];

                course_start = response['result']['results'][i]['start_date'];
                course_discount_applicable = response['result']['results'][i]['discount_applicable'];
                course_price = response['result']['results'][i]['modes'][0]['price'];
                course_discount_type = response['result']['results'][i]['discount_type'];
                course_discounted_price = response['result']['results'][i]['discounted_price'];
                course_discount_percentage = response['result']['results'][i]['discount_percentage'];

                var course = `<li class="card-slider-card-items owl-item">
               <article class="card-slider-course">
                  <a href="/courses/`+course_code+`/about">
                     <header class="card-slider-card-img-cont">
                        <div class="card-slider-card-cover-img">
                           <img src="` + course_image + `" alt="` + course_name + `">
                           <div class="card-slider-card-learn-more-btn" aria-hidden="true">LEARN MORE</div>
                        </div>
                     </header>
                     <div class="card-slider-card-course-info" aria-hidden="true">
                        <h2 class="crd-sldr-course-info ">
                           <span class="crd-sldr-course-info-org">` + course_org + `</span>
                           <span class="crd-sldr-course-info-code fl">` + course_id + `</span>
                           <span class="crd-sldr-course-info-title">` + course_name + `</span>
                           <p class="crd-sldr-course-info-label">Difficulty Level:<span class="course-difficulty_level">` + course_difficulty_level + `</span></p>
                           <p class="crd-sldr-course-info-label">Enrollment Count:<span class="course-enrollments_count">` + course_enrollments_count + `</span></p>
                           <p class="crd-sldr-course-info-label">Rating:<span class="course-ratings">` + course_ratings + `</span></p>
                           <p class="crd-sldr-course-info-label">Comments Count:<span class="course-comments_count">` + course_comments_count + `</span></p>

                           <div class="crd-sldr-course-info-price fl">
                              <ul>`
                                  if (course_discount_applicable == true)
                                {
                                    if (course_discount_type == 'Percentage'){
                                 course +=`<li>Discount Percentage: <span class="main_price-percentage">`+course_discount_percentage+`%</span></li>`
                                 }
                                 else {
                                    course +=`<li>Discount: <span class="main_price-percentage">S$`+course_discount_percentage+`</span></li>`
                                 }

                                 course +=`<li>Price: <span class="crd-sldr-course-info-main-price main_price_cut">  ` + course_price + ` </span></li>
                                 <li>Discounted Price: <span class="main_price">S$`+course_discounted_price+`</span></li>`
                                }
                                else if (course_discount_applicable == false && course_price > 0 )
                                {

                                    course +=`<li>Price: <span class="main_price">S$`+course_price+`</span></li>`
                                }
                                else
                                {
                                    course +=`<li>Price: <span class="main_price">Free</span></li>`
                                }

                                course +=`

                              </ul>
                           </div>`

                           available_vouchers = response['result']['results'][i]['available_vouchers'];
                           if (available_vouchers.length > 0)
                                {
                                   course+=`<div class="coupon_details">`
                                  for (var j=0; j < available_vouchers.length; j++)
                                  {
                                        if (available_vouchers[j]["discount_type"] == 'Absolute')
                                        {

                                           course+= `<p><span class="coupen_code_value"><i class="fa fa-check"></i>`+ available_vouchers[j]["code"] +` -S$` + available_vouchers[j]["discount_value"]+`</span></p>`
                                        }
                                        else
                                        {

                                         course+=   `<p><span class="coupen_code_value"><i class="fa fa-check"></i>` +available_vouchers[j]["code"]+ ` -`+available_vouchers[j]["discount_value"]+`%</span></p>`
                                        }
                                    }
                            course+=`</div>`
                        }

                        course+=`</h2>
                        <div class="crd-sldr-course-info-date" aria-hidden="true" data-format="shortDate" data-datetime="2013-02-05T05:00:00+0000" data-language="en" data-string="Starts: {date}">Starts: ` + course_start + `</div>
                     </div>
                  </a>
               </article>
            </li>`;


                $("#top_rated_ul").append(course)

            }

        var viewedSlider_top = $('#top_rated_ul');
        viewedSlider_top.owlCarousel({
        loop: false,
        margin: 20,
        autoplay: false,
        autoplayTimeout: 6000,
        dots: false,
        items: 4,
        slideBy: 4,
        responsive:
            {
            0:{items:1},
            768:{items:2},
            991:{items:4}
            }
        });

        }
    });

}

function show_recommended_courses(target) {

        var recommended_settings = {
        "url": target,
        "method": "GET",
        "headers": {
            'X-CSRFToken': $('#web_csrf_token').val()
        },
        "processData": false,

        "contentType": false,
    };

    $("#recommended_courses_loader").css("display", "");
    $.ajax(recommended_settings).done(function(response) {
    $('#recommended_courses_ul').owlCarousel('destroy');
    $("#recommended_courses_ul ").html('');
        $("#recommended_courses_loader").css("display", "None")
        console.log(response);
        if (response['status_code'] == 200) {
            $('.courses-listing').empty()
            pagination_next_url = response['result']['pagination']["next"];

            if (pagination_next_url != null){
                $("#recommended_next_btn").css("display","");
                recommended_next_url = pagination_next_url;
            }
            else {
            $("#recommended_next_btn").css("display","None")
            }
            if (response['result']['pagination']['previous'] != null){
                $("#recommended_prev_btn").css("display","");
                recommended_prev_url = response['result']['pagination']['previous'];
            }


            for (var i = 0; i < response['result']['results'].length; i++) {
                course_id = response['result']['results'][i]['course_number'];
                course_org = response['result']['results'][i]['organization'];
                course_code = response['result']['results'][i]['id'];
                course_name = response['result']['results'][i]['name'];
                course_image = response['result']['results'][i]["media"]['image']["raw"];
                course_difficulty_level = response['result']['results'][i]['difficulty_level'];
                course_enrollments_count = response['result']['results'][i]['enrollments_count'];
                course_ratings = response['result']['results'][i]['ratings'];
                course_ratings = course_ratings !== null ? course_ratings : "None";
                course_comments_count = response['result']['results'][i]['comments_count'];

                course_start = response['result']['results'][i]['start_date'];
                course_discount_applicable = response['result']['results'][i]['discount_applicable'];
                course_price = response['result']['results'][i]['modes'][0]['price'];
                course_discount_type = response['result']['results'][i]['discount_type'];
                course_discounted_price = response['result']['results'][i]['discounted_price'];
                course_discount_percentage = response['result']['results'][i]['discount_percentage'];

                var course = `<li class="card-slider-card-items owl-item">
               <article class="card-slider-course">
                  <a href="/courses/`+course_code+`/about">
                     <header class="card-slider-card-img-cont">
                        <div class="card-slider-card-cover-img">
                           <img src="` + course_image + `" alt="` + course_name + `">
                           <div class="card-slider-card-learn-more-btn" aria-hidden="true">LEARN MORE</div>
                        </div>
                     </header>
                     <div class="card-slider-card-course-info" aria-hidden="true">
                        <h2 class="crd-sldr-course-info ">
                           <span class="crd-sldr-course-info-org">` + course_org + `</span>
                           <span class="crd-sldr-course-info-code fl">` + course_id + `</span>
                           <span class="crd-sldr-course-info-title">` + course_name + `</span>
                           <p class="crd-sldr-course-info-label">Difficulty Level:<span class="course-difficulty_level">` + course_difficulty_level + `</span></p>
                           <p class="crd-sldr-course-info-label">Enrollment Count:<span class="course-enrollments_count">` + course_enrollments_count + `</span></p>
                           <p class="crd-sldr-course-info-label">Rating:<span class="course-ratings">` + course_ratings + `</span></p>
                           <p class="crd-sldr-course-info-label">Comments Count:<span class="course-comments_count">` + course_comments_count + `</span></p>

                           <div class="crd-sldr-course-info-price fl">
                              <ul>`
                                  if (course_discount_applicable == true)
                                {
                                    if (course_discount_type == 'Percentage'){
                                 course +=`<li>Discount Percentage: <span class="main_price-percentage">`+course_discount_percentage+`%</span></li>`
                                 }
                                 else {
                                    course +=`<li>Discount: <span class="main_price-percentage">S$`+course_discount_percentage+`</span></li>`
                                 }

                                 course +=`<li>Price: <span class="crd-sldr-course-info-main-price main_price_cut">  ` + course_price + ` </span></li>
                                 <li>Discounted Price: <span class="main_price">S$`+course_discounted_price+`</span></li>`
                                }
                                else if (course_discount_applicable == false && course_price > 0 )
                                {

                                    course +=`<li>Price: <span class="main_price">S$`+course_price+`</span></li>`
                                }
                                else
                                {
                                    course +=`<li>Price: <span class="main_price">Free</span></li>`
                                }

                                course +=`

                              </ul>
                           </div>`

                           available_vouchers = response['result']['results'][i]['available_vouchers'];
                           if (available_vouchers.length > 0)
                                {
                                   course+=`<div class="coupon_details">`
                                  for (var j=0; j < available_vouchers.length; j++)
                                  {
                                        if (available_vouchers[j]["discount_type"] == 'Absolute')
                                        {

                                           course+= `<p><span class="coupen_code_value"><i class="fa fa-check"></i>`+ available_vouchers[j]["code"] +` -S$` + available_vouchers[j]["discount_value"]+`</span></p>`
                                        }
                                        else
                                        {

                                         course+=   `<p><span class="coupen_code_value"><i class="fa fa-check"></i>` +available_vouchers[j]["code"]+ ` -`+available_vouchers[j]["discount_value"]+`%</span></p>`
                                        }
                                    }
                            course+=`</div>`
                        }

                        course+=`</h2>
                        <div class="crd-sldr-course-info-date" aria-hidden="true" data-format="shortDate" data-datetime="2013-02-05T05:00:00+0000" data-language="en" data-string="Starts: {date}">Starts: ` + course_start + `</div>
                     </div>
                  </a>
               </article>
            </li>`;


                $("#recommended_courses_ul").append(course)

            }
            var viewedSlider_rec = $('#recommended_courses_ul');

            viewedSlider_rec.owlCarousel({
                loop: true,
                margin: 20,
                autoplay: false,
                autoplayTimeout: 6000,
                dots: false,
                items: 4,
                slideBy: 4,
                responsive:
                {
                0:{items:1},
                768:{items:2},
                991:{items:4}
                }
        });
        }
    });

}

$(document).ready(function() {
    // Recommended Courses Slider Button
    // From here
    if ($('#recommended_prev_btn').length) {
        var prev = $('#recommended_prev_btn');
        prev.on('click', function() {
            viewedSlider_rec.trigger('prev.owl.carousel');
            show_recommended_courses(recommended_prev_url);
            $('#recommended_prev_btn').show();
        });
    }
    if ($('#recommended_next_btn').length) {
        var next = $('#recommended_next_btn');
        next.on('click', function() {
            viewedSlider_rec.trigger('next.owl.carousel');
            show_recommended_courses(recommended_next_url);
            $('#recommended_next_btn').show();
        });
    }
    // till here
    
    
    // Most Popular Courses Slider Button
    // From here
    if ($('#popular_prev_btn').length) {
        var prev = $('#popular_prev_btn');
        prev.on('click', function() {
            show_most_popular_courses(popular_prev_url);
            viewedSlider_pop.trigger('prev.owl.carousel');
            $('#popular_prev_btn').show();
        });
    }
    if ($('#popular_next_btn').length) {
        var next = $('#popular_next_btn');
        next.on('click', function() {
            show_most_popular_courses(popular_next_url);
            viewedSlider_pop.trigger('next.owl.carousel');
            $('#popular_next_btn').show();
        });
    }
    // till here
    
    // Free Courses Slider Button
    // From here
    if ($('#free_prev_btn').length) {
    var prev = $('#free_prev_btn');
    prev.on('click', function() {
        viewedSlider_free.trigger('prev.owl.carousel');
        show_free_courses(free_prev_url);
        $('#free_prev_btn').show();
    });
    }
    if ($('#free_next_btn').length) {
        var next = $('#free_next_btn');
        next.on('click', function() {
            viewedSlider_free.trigger('next.owl.carousel');
            show_free_courses(free_next_url);
            $('#free_next_btn').show();
        });
    }
    
    // till here

    // Bundled Courses Slider Button
    // From here
    if ($('#bundled_prev_btn').length) {
        var prev = $('#bundled_prev_btn');
        prev.on('click', function() {
            viewedSlider_bundled.trigger('prev.owl.carousel');
            show_bundled_courses(bundled_prev_url);
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
    
    // Top Rated Courses Slider Button
    // From here
    if ($('#top_prev_btn').length) {
        var prev = $('#top_prev_btn');
        prev.on('click', function() {
            show_top_rated_courses(top_prev_url);
            viewedSlider_top.trigger('prev.owl.carousel');
            $('#top_prev_btn').show()
        });
    }
    if ($('#top_next_btn').length) {
        var next = $('#top_next_btn');
        next.on('click', function() {
            show_top_rated_courses(top_next_url);

            viewedSlider_top.trigger('next.owl.carousel');
            $('#top_next_btn').show();
        });
    } 
       
    // Till here
    
    show_most_popular_courses(window.location.protocol + '//' + window.location.host + "/api/commerce/v2/web/courses/?platform_visibility=web&ordering=-enrollments_count&page=1&page_size=4");
    show_free_courses(window.location.protocol + '//' + window.location.host + "/api/commerce/v2/web/courses/?platform_visibility=web&sale_type=free&page=1&page_size=4");
    show_bundled_courses(window.location.protocol + '//' + window.location.host + "/api/subscriptions/featured-plans/");
    show_top_rated_courses(window.location.protocol + '//' + window.location.host + "/api/commerce/v2/web/courses/?platform_visibility=web&ordering=-ratings&page=1&page_size=4");
    
    });
    