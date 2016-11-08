var dates = [];
var maindata = null;
var products = ["Firefox", "FennecAndroid"];
var product = products[0];
var channel = "nightly";
var curdate = null;

function init_patches() {
    $.get("http://localhost/clouseau/rest/patches", populate_dates, 'json');
    populate_product();
}

function update(data) {
    maindata = data;
    first = populate_signatures(data);
    make_tables(first, data[first]);
}

function make_patch(patches) {
    var td = $("<td></td>");
    if (patches.length == 0) {
        return td;
    }
    var ul = $("<ul></ul>");
    for (var patch of patches) {
        var node = patch.node;
        var link = "http://hg.mozilla.org/mozilla-central/rev?node=" + node;
        var partial_node = node.substring(0, 13); 
        var date = patch.pushdate;
        var li = $("<li><a href='" + link + "'>" + partial_node + "</a>&nbsp;at&nbsp;" + date + "</li>");
        ul.append(li);
    }
    td.attr("class", "success");
    td.append(ul);
    return td;
}

function make_table(bt, total) {
    var count = bt.count;
    var uuid = bt.uuids[0];
    var div1 = $("<div></div>");
    var div2 = $("<div class='well'></div>");
    var div3 = $("<div class='container'></div>");
    var p1 = $("<p>This backtrace represents " + Math.round(100. * count / total) + "% of the different backtraces (total is " + total + ").</p>");
    var link = "https://crash-stats.mozilla.com/report/index/" + uuid;
    var p2 = $("<p>The report <a href='" + link + "'>" + uuid + "</a> has it.</p>");
    div2.append(p1);
    div2.append(p2);
    div1.append(div2);
    var table = $("<table class='table table-bordered container'></table>");
    var thead = $("<thead><tr><th>Functions</th><th>Files</th><th>Patches</th></tr></thead>");
    var tbody = $("<tbody></tbody>");
    for (var bti of bt.bt) {
        var tr = $("<tr></tr>");
        var func = bti[0];
        var file = bti[1].filename;
        var patches = bti[1].patches;
        tr.append($("<td>" + func + "</td>"));
        tr.append($("<td>" + file + "</td>"));
        tr.append(make_patch(patches));
        tbody.append(tr);
    }
    table.append(thead);
    table.append(tbody);
    div3.append(table);
    div1.append(div3);
    return div1;
}

function get_total(bts) {
    var total = 0;
    for (var bt of bts) {
        total += bt.uuids.length;
    }
    return total;
}

function make_title() {
    document.title  = "Backtraces and patches in " + product + " - " + curdate;
}

function make_tables(sgn, bts) {
    var panel = $("<div class='panel panel-default'></div>");
    var heading = $("<div class='panel-heading'>Backtraces for signature &lsquo;<span id='signature'></span>&rsquo;</div>");
    heading.children("#signature").text(sgn);
    panel.append(heading);
    bts = bts.sort(function (bt1, bt2) { return bt2.uuids.length - bt1.uuids.length; });
    for (var bt of bts) {
        var div = $("<div></div>");
        var table = make_table(bt, get_total(bts));
        div.append(table);
        panel.append(div);
    }
    var main = $("#main");
    main.empty();
    main.append(panel);
}

function dates_cb(date) {
    curdate = date;
    $.get("http://localhost/clouseau/rest/patches",
          {"channel": channel, "product": product, "date": date},
          update, 'json');
    make_title();
}

function populate_dates(data) {
    dates = data.dates;
    $("#datesbutton").empty();
    for (var date of dates) {
        var li = $("<li></li>");
        var a = $("<a href=\'#\'></a>");
        a.text(date);
        a.click(function(e){dates_cb(e.target.text); return true;});
        li.append(a);
        $("#datesbutton").append(li);
    }
    dates_cb(dates[0]);
}

function show_signature(sgn) {
    make_tables(sgn, maindata[sgn]);
}

function populate_signatures(data) {
    $("#sgnsbutton").empty();
    sgns = []
    for (var sgn in data) {
        sgns.push([sgn, get_total(data[sgn])]);
    }
    sgns = sgns.sort(function (a, b) { var d = b[1] - a[1]; if (d != 0) return d; else return a[0].localeCompare(b[0]); });
    for (var sgn of sgns) {
        sgn = sgn[0];
        var li = $("<li></li>");
        var a = $("<a href=\'#\'></a>");
        a.text(sgn);
        a.click(function(e){show_signature(e.target.text); return true;});
        li.append(a);
        $("#sgnsbutton").append(li);
    }

    return sgns[0][0];
}

function products_cb(prod) {
    product = prod;
    $.get("http://localhost/clouseau/rest/patches",
          {"channel": channel, "product": product, "date": curdate},
          update, 'json');
    make_title();
}

function populate_product() {
    $("#productsbutton").empty();
    for (var prod of products) {
        var li = $("<li></li>");
        var a = $("<a href=\'#\'></a>");
        a.text(prod);
        a.click(function(e){products_cb(e.target.text); return true;});
        li.append(a);
        $("#productsbutton").append(li);
    }
}
