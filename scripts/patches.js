var dates = [];
var maindata = null;
var product = "Firefox";
var channel = "nightly";

function init_patches() {
    $.get("http://localhost/clouseau/rest/patches", populate_dates, 'json');
}

function update(data) {
    maindata = data;
    populate_signatures(data);
    for (var sgn in data) {
        make_tables(sgn, data[sgn]);
        break;
    }
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
    td.append(ul);
    return td;
}

function make_table(bt, total) {
    var count = bt.count;
    var uuid = bt.uuids[0];
    var div = $("<div></div>");
    var p1 = $("<p>This backtrace represents " + Math.round(100. * count / total) + "% of the different backtraces (total is " + total + ").</p>");
    var link = "https://crash-stats.mozilla.com/report/index/" + uuid;
    var p2 = $("<p>The report <a href='" + link + "'>" + uuid + "</a> has it.</p>");
    div.append(p1);
    div.append(p2);
    var table = $("<table class='table table-bordered'></table>");
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
    div.append(table);
    return div;
}

function get_total(bts) {
    var total = 0;
    for (var bt of bts) {
        total += bt.uuids.length;
    }
    return total;
}

function make_tables(sgn, bts) {
    var panel = $("<div class='panel panel-default'></div>");
    var heading = $("<div class='panel-heading'>Backtraces for signature &lsquo;<span id='signature'></span>&rsquo;</div>");
    heading.children("#signature").text(sgn);
    panel.append(heading);
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
    $.get("http://localhost/clouseau/rest/patches",
          {"channel": channel, "product": product, "date": date},
          update, 'json');
    document.title  = "Backtraces and patches - " + date;
}

function populate_dates(data) {
    dates = data.dates;
    $("#datesbutton").empty()
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
    for (var sgn in data) {
        var li = $("<li></li>");
        var a = $("<a href=\'#\'></a>");
        a.text(sgn);
        a.click(function(e){show_signature(e.target.text); return true;});
        li.append(a);
        $("#sgnsbutton").append(li);
    }
}
