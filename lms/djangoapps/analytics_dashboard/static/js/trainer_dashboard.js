

const year_label = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
var years = [{% for k,val in trainer_course_year.items %} '{{ k | safe }}', {% endfor %}]
var course_count_data = [{% for k,val in trainer_course_year.items %} [{% for k,v in val.items %}'{{ v | safe }}', {% endfor %}], {% endfor %}]
var ctx = document.getElementById('numberOfCoursesChart')
// eslint-disable-next-line no-unused-vars
console.log('couse data', {{ trainer_course_year | safe }})

console.log('cslen', course_count_data.length)

function genRand(min, max, decimalPlaces) {
    return (Math.random() * (max - min) + min).toFixed(decimalPlaces) * 1;
}

var ds = []
var rgb_colors = [
    'rgba(255,102,102, 1)',
    'rgba(255,178,102, 1)',
    'rgba(255,255,102, 1)',
    'rgba(178,255,102, 1)',
    'rgba(102,255,102, 1)',
    'rgba(102,255,178, 1)',
    'rgba(102,255,255, 1)',
    'rgba(102,178,255, 1)',
    'rgba(102,102,255, 1)',
    'rgba(178,102,255, 1)',
    'rgba(255,102,255, 1)',
    'rgba(255,102,178, 1)',
    ]
for (i = 0; i < course_count_data.length; i++){
const clr = genRand;
console.log(clr);
        ds.push(
            {
                label: years[i],
                data: course_count_data[i],
                //backgroundColor: 'rgba(' + 49 + ',' + 107 + ',' + 196 + ',' + genRand(0.3, 1.0, 1) + ')',
                borderColor: clr + 0.6 + ')',
                backgroundColor: clr + 1 + ')',
            },
        )
}
console.log('dataset', ds)


const numberOfCoursesChartLabels = year_label;
const numberOfCoursesChartData = {
    labels: numberOfCoursesChartLabels,
    datasets: ds
};

var myChart = new Chart(ctx, {
    type: 'line',
    data: numberOfCoursesChartData,
    options: {
        responsive: true,
        parsing: {
            xAxisKey: 'id',
            yAxisKey: 'nested.value'
        },
        plugins: {
            legend: {
                position: 'top',
            },
            title: {
                display: true,
                text: 'Students enrolled by year'
            }
        }
    },


})