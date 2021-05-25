$(document).ready(function() {

    (async ()=>{
    await show_basket();
    var tax_percent = 0;
    var is_basket_empty = true;
    get_recommended_courses();
    onclick_select();
    })();

    add_checkout_function();
    });

    // converts price to 2 decimal points e.g 2.1 to 2.10
    function append_decimal(price){
        return (price).toFixed(2);
    }

    function show_basket()
    {
    $('#loader-sec').css('display', '')
    return $.ajax({
    type:"GET",
    url: "/api/commerce/v2/basket-details/",
    data: JSON.stringify({
    "products":[{"sku":$('#course_sku').val()}],
    csrfmiddlewaretoken: $('#web_csrf_token').val()
    }),
    contentType: "application/json; charset=utf-8",
    success: function(response){
    var course_id = '';
    if (response['status_code'] == 200)
    {
    $('.wish-list').empty()
    response['result']['basket_total'] = append_decimal(response['result']['basket_total']);
    if (response['result']['products'].length > 0)
    {
      is_basket_empty = false;
    }
    else
    {
      is_basket_empty = true;
    }


    for (var i = 0; i < response['result']['products'].length; i++)
    {

    for (var j=0; j< response['result']['products'][i].length; j++)
    {
    var course_details = {}

    if (response['result']['products'][i][j]['code'] == "course_details")
    {
    course_details = response['result']['products'][i][j]
    if (course_details['discount_applicable'] == true)
    {
    course_details['discounted_price'] = append_decimal(course_details['discounted_price'])
    }
    else
    {
    course_details['price'] = append_decimal(course_details['price'])
    }
    }
    if(response['result']['products'][i][j]['code'] == "course_key")
    {
    course_id = response['result']['products'][i][j]['value']
    }
    }
    b = `<div class="form-check">
    <input class="form-check-input" type="checkbox" checked=checked data-sku="`+course_details['sku']+`">
    </div>
    <div class="row cart-list" >
    <div class="col-md-5 col-lg-3 col-xl-3 px-4 rounded img-container">
    <img class="img-fluid" src="`+course_details['media']['raw']+`" alt="Sample" style="
    max-height: 150px;
    width: 100%;
    border-radius: 25px !important;
    ">
    </div>
    <div class="col-md-7 col-lg-9 col-xl-9">
    <div>
    <div class="d-inline float-left col-8 pt-4 mt-2">
    <div>
    <h5>`+course_details['title']+`</h5>
    <p class="mb-2 text-muted small">`+course_details['organization']+`</p>
    <p class="mt-2 text-muted small">`+course_details['category']+`</p>
    </div>
    </div>
    <div class="d-inline float-left col-2 pt-4">
    <div>
    </div>`
    if (course_details['discount_applicable'] == true)
    {
    b+=`<div class="price-set">`
    b+=`<p class="mb-0"><span><strong id="summary" style="color: #ff6161;font-weight: 800;">S$`+course_details['discounted_price']+`</strong></span></p>`
    b+=`<p class="m-0"><span><strong id="summary" style="
    color: #8a8a8a;
    font-weight: 500;
    text-decoration: line-through;
    ">S$`+course_details['price']+`</strong></span></p>`
    b+=`</div>`
    }
    else
    {
    b+=`<div class="price-set">`
    b+=`<p class="mb-0"><span><strong id="summary" style="color: #ff6161;font-weight: 800;"></strong></span></p>`
    b+=`<p class="m-0"><span><strong id="summary" style="color: #ff6161;font-weight: 800;">S$`+course_details['price']+`</strong></span></p>`
    b+=`</div>`
    }
    b+=`
    </div>
    <div class="d-inline float-left col-2 pt-4">
    <button class="btn-remove" data-courseid=`+course_id+` style="
    background: transparent;
    box-shadow: none;
    "><i class="fa fa-trash" style="
    color: #8a8a8a;
    "></i>
    </button>
    <div>
    </div>
    </div>
    </div>
    </div>


    </div>`
    $('.wish-list').append(b)
    }
    add_remove_click_function();
    }
    var sub_total = response['result']['basket_total_excl_tax'];
    sub_total = append_decimal_point(sub_total)
    $('.list-group').empty();
    $('.list-group').append(`<li class="list-group-item d-flex justify-content-between align-items-center border-0 px-0 pb-0 font-weight-bold bg-transparent color">Sub Total<span id="sub_total">S$`+sub_total+`</span></li>`)
    $('.list-group').append(`<li class="list-group-item d-flex justify-content-end align-items-center px-0 bg-transparent border-0">
    </li>
    `)

    tax_percent = response['result']['tax_percent']
    var tax = response['result']['tax']
    tax = append_decimal_point(tax)
    $('.list-group').append(`<li id="tax" class="list-group-item d-flex justify-content-between align-items-center border-0 px-0 mb-3 bg-transparent">
    <div>
    <strong class="color">GST `+tax_percent+`%</strong>
    </div>
    <span><strong id="total_tax" class="color">S$`+tax+`</strong></span>
    </li>`)



    $('.list-group').append(`<li id="total" class="list-group-item d-flex justify-content-between align-items-center border-0 px-0 mb-3 bg-transparent">
    <div>
    <strong class="color">Total</strong>
    </div>
    <span><strong id="cart_total" class="color">S$`+response['result']['basket_total']+`</strong></span>
    </li>
    `)
    if (is_basket_empty == true)
    {
      $('#btn-checkout').attr("disabled", true)

    }
    else
    {
      $('#btn-checkout').attr("disabled", false)
    }
    $('#loader-sec').css('display', 'none')
    //else if (response['status_code'] == 500)
    //{
    //alert(response['message']);
    //}

    },
    error: function(data) {
    }
    })



    }



    function add_remove_click_function()
    {
    $(".btn-remove").click(function(){

    $('#loader-sec').css('display', '')
    $.ajax({
    type:"POST",
    url: "/api/stripe/basket/remove_item/", // + "?course_id=course-v1:edx+cs8789+2021-t1",
    data: {
    'course_id':$(this).attr('data-courseid'),
    csrfmiddlewaretoken: $('#web_csrf_token').val()
    },
    //datatype:"json",
    //jsonp: "jsonp",
    //contentType: "application/json; charset=utf-8",
    success: function(response){
    if (response['status_code'] == 200)
    {
      show_basket();}
    }
    });

    });

    }

    function add_checkout_function()
    {

    $("#btn-checkout").click(function(){

    $('#loader-sec').css('display', '')
    var selected_skus = $(".form-check-input:checked").map(function () {
    return {'sku':$(this).data('sku')}
    }).get();;
    $.ajax({
    type:"POST",
    url: "/api/stripe/basket/buy_now/",
    data: JSON.stringify({
    'products':selected_skus,
    csrfmiddlewaretoken: $('#web_csrf_token').val()
    }),
    contentType: "application/json",
    success: function(response){
    if (response['status_code'] == 200)
    {
    $('#loader-sec').css('display', 'none')
    window.location.href = $('#ecommerce_url').val() + "/basket"
    }

    else
    {
    $('#loader-sec').css('display', 'none')
    alert(response['message']);
    }

    }
    });

    });

    }

    function append_decimal_point(price){
        str_price = price.toString()
        split_price = str_price.split(".")
        if(split_price.length === 2){
            last_decimal_point = split_price[split_price.length-1]
            if(!(last_decimal_point.length >= 2)){
                str_price = str_price.concat("0")
                return str_price
            }
            else{
                return price.toFixed(2)
            }
        }
        else{
            return str_price.concat(".00")
        }
    }
    function onclick_select()

    {
    //$('#loader-sec').css('display', '')

    $(".form-check-input").change(function(){

    $('#loader-sec').css('display', '')
    //Set timeout is needed because without this, execution is so fast that user will not be able to know that cart total has been updated
    setTimeout(
    function()
    {
    var selected = $(".form-check-input:checked")
    var cart_total = 0.00;
    for (var x=0; x<selected.length; x++)
    {
    var x_selected = selected[x]
    var cart_list = $(x_selected).parent().next();
    var price_elements = $(cart_list.children().find('.price-set').find('p')[0]).text().length > 0 ? cart_list.children().find('.price-set').find('p')[0] : cart_list.children().find('.price-set').find('p')[1]

    var price_text = $(price_elements).text();
    var price = price_text.substring(2, price_text.length);
    var float_price = parseFloat(price);
    cart_total += float_price
    }
    var currency = 'S$'
    var two_decimal_price = append_decimal_point(cart_total)
    var total = currency.concat(two_decimal_price)
    var tax = two_decimal_price * tax_percent/100
    var tax = tax.toFixed(2)
    var updated_cart_total = ((+two_decimal_price) + (+tax)).toFixed(2)
    var updated_cart_total = currency.concat(updated_cart_total)
    var tax = currency.concat(tax)

    $("#cart_total").text(updated_cart_total)
    $("#sub_total").text(total)
    $("#total_tax").text(tax)
    if (selected.length == 0)
    {
    $('#btn-checkout').attr("disabled", true)
    }
    else
    {
    $('#btn-checkout').attr("disabled", false)
    }

    $('#loader-sec').css('display', 'none')
    }, 1000);

    });


    }







    function get_recommended_courses()
    {

    $.ajax({
    type:"GET",
    url: "/api/courses/v2/web_recommended/courses/",
    //data: JSON.stringify({
    //"products":[{"sku":$('#course_sku').val()}],
    //csrfmiddlewaretoken: $('#web_csrf_token').val()
    //}),
    contentType: "application/json; charset=utf-8",
    success: function(response){
    if (response['status_code'] == 200)
    {
    $('#heading_recommended_courses').css('display','')
    $('.courses-listing').empty()
    for (var i=0; i <=2; i++)
    {
    course_id = response['result']['result'][i]['id']
    course_org = response['result']['result'][i]['org']
    course_code = response['result']['result'][i]['code']
    course_name = response['result']['result'][i]['name']
    course_image = response['result']['result'][i]['image']
    course_difficulty_level = response['result']['result'][i]['difficulty_level']
    course_enrollments_count = response['result']['result'][i]['enrollments_count']
    course_ratings = response['result']['result'][i]['ratings']
    course_ratings = course_ratings !== null ? course_ratings : "None"
    course_comments_count = response['result']['result'][i]['comments_count']

    course_start = response['result']['result'][i]['start']
    course_discount_applicable = response['result']['result'][i]['discount_applicable']
    course_price = response['result']['result'][i]['price']
    course_discounted_price = response['result']['result'][i]['discounted_price']
    course_discount_percentage = response['result']['result'][i]['discount_percentage']
    course_discount_type = response['result']['result'][i]['discount_type']
    

    
    var course = `<li class="courses-listing-item">
    <article class="course" id="`+course_id+`" role="region" aria-label="`+course_name+`">
    <a href="/courses/`+course_id+`/about">
    <header class="course-image">
    <div class="cover-image">
    <img src="`+course_image+`" alt="`+course_name+`">
    <div class="learn-more" aria-hidden="true">LEARN MORE</div>
    </div>
    </header>
    <div class="course-info" aria-hidden="true">
    <h2 class="course-name d-flex">
    <span class="course-organization">`+course_org+`</span>
    <span class="course-code fl">`+course_code+`</span>
    <span class="course-title">`+course_name+`</span>
    <p class="coure-label">Difficulty Level:<span class="course-difficulty_level">`+course_difficulty_level+`</span></p>
    <p class="coure-label">Enrollment Count:<span class="course-enrollments_count">`+course_enrollments_count+`</span></p>
    <p class="coure-label">Rating:<span class="course-ratings">`+course_ratings+`</span></p>
    <p class="coure-label">Comments Count:<span class="course-comments_count">`+course_comments_count+`</span></p>
    <div class="price_details fl">
    <ul>`
    if (course_discount_applicable == true)
    {
    if (course_discount_type == 'Percentage')
    {
    course +=`<li>Discount Percentage: <span class="main_price-percentage">`+course_discount_percentage+`%</span></li>
    <li>Price: <span class="main_price_cut">S$`+course_price+`</span></li>
    <li>Discounted Price: <span class="main_price">S$`+course_discounted_price+`</span></li>`
    }
    else{
        course +=`<li>Discount: <span class="main_price-percentage">`+course_discount_percentage+`</span></li>
    <li>Price: <span class="main_price_cut">S$`+course_price+`</span></li>
    <li>Discounted Price: <span class="main_price">S$`+course_discounted_price+`</span></li>`
    }
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

           available_vouchers = response['result']['result'][i]['available_vouchers']

           if (available_vouchers.length > 0)
                {
                   course+=`<div class="coupon_details">` 
                  for (var j=0; j < available_vouchers.length; j++)
                  {  
                        if (available_vouchers[j]["incentive_type"] == 'Absolute')
                        {
                    
                           course+= `<p><span class="coupen_code_value"><i class="fa fa-check"></i>`+ available_vouchers[j]["coupon_code"] +` -S$` + available_vouchers[j]["incentive_value"]+`</span></p>`
                        }
                        else
                        {    

                         course+=   `<p><span class="coupen_code_value"><i class="fa fa-check"></i>` +available_vouchers[j]["coupon_code"]+ ` -`+available_vouchers[j]["incentive_value"]+`%</span></p>`
                        }    
                    }
            course+=`</div>`
        }

        course+=`</h2>
    <div class="course-date localized_datetime" aria-hidden="true" data-format="shortDate" data-datetime="2013-02-05T05:00:00+0000" data-language="en" data-string="Starts: {date}">Starts: `+course_start+`</div>
    </div>
    </a>
    </article>
    </li>
    `
    $('.courses-listing').append(course)
    }
    }
    }
    });

    }
