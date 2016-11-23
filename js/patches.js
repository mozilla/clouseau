/*jslint browser:true */
/*global $, jQuery*/

"use strict";

var maindata = null;
var product = "";
var curchan = "";
var curdate = "";

function make_title() {
    document.title  = "Backtraces and patches in " + product + " - " + curdate;
}

function get_total(bts) {
    var total = 0;
    for (var bt of bts) {
        total += bt.count;
    }
    return total;
}

function make_patch(patches) {
    if (patches.length === 0) {
        return $("<td></td>");
    }
    var td = $("<td></td>"),
        ul = $("<ul></ul>");
    for (let patch of patches) {
        let node = patch.node,
            link = "http://hg.mozilla.org/mozilla-central/rev?node=" + node,
            partial_node = node.substring(0, 13),
            date = patch.pushdate,
            li = $("<li><a href='" + link + "'>" + partial_node + "</a>&nbsp;at&nbsp;" + date + "</li>");
        ul.append(li);
    }
    td.attr("class", "success");
    td.append(ul);
    return td;
}

function make_table(bt, total) {
    var count = bt.count,
        uuid = bt.uuids[0],
        div1 = $("<div></div>"),
        div2 = $("<div class='well'></div>"),
        div3 = $("<div class='container'></div>"),
        p1 = $("<p>This backtrace represents " + Math.round(100.0 * count / total) + "% of the different backtraces (total is " + total + ").</p>"),
        link = "https://crash-stats.mozilla.com/report/index/" + uuid,
        p2 = $("<p>The report <a href='" + link + "'>" + uuid + "</a> has it.</p>"),
        table = $("<table class='table table-bordered container'></table>"),
        thead = $("<thead><tr><th>Functions</th><th>Files</th><th>Patches</th></tr></thead>"),
        tbody = $("<tbody></tbody>");
    div2.append(p1);
    div2.append(p2);
    div1.append(div2);
    for (let bti of bt.bt) {
        let tr = $("<tr></tr>"),
            func = bti[0],
            file = bti[1].filename,
            node = bti[1].node,
            line = bti[1].line,
            patches = bti[1].patches,
            hgurl = "https://hg.mozilla.org/mozilla-central/annotate/" + node + "/" + file + "#l" + line;
        tr.append($("<td>" + func + "</td>"));
        tr.append($("<td><a href='" + hgurl + "'>" + file + "</a></td>"));
        tr.append(make_patch(patches));
        tbody.append(tr);
    }
    table.append(thead);
    table.append(tbody);
    div3.append(table);
    div1.append(div3);
    return div1;
}

function make_tables(sgn, bts) {
    var panel = $("<div class='panel panel-default'></div>"),
        heading = $("<div class='panel-heading'>Backtraces for signature &lsquo;<span id='signature'></span>&rsquo;</div>"),
        main = $("#main");
    heading.children("#signature").text(sgn);
    panel.append(heading);
    bts = bts.sort(function (bt1, bt2) { return bt2.count - bt1.count; });
    for (let bt of bts) {
        let div = $("<div></div>"),
            table = make_table(bt, get_total(bts));
        div.append(table);
        panel.append(div);
    }
    main.empty();
    main.append(panel);
}

function show_signature(sgn) {
    $("#signaturestitle").text(sgn);
    make_tables(sgn, maindata[sgn]);
}

function populate_signatures(data) {
    $("#sgnsbutton").empty();
    var sgns = [],
        cb = function (e) { show_signature(e.target.text); return true; };
    for (let sgn in data) {
        sgns.push([sgn, get_total(data[sgn])]);
    }
    sgns = sgns.sort(function (a, b) { var d = b[1] - a[1]; if (d != 0) { return d; } return a[0].localeCompare(b[0]); });
    for (let sgn of sgns) {
        let li = $("<li></li>"),
            a = $("<a href=\'#\'></a>");
        sgn = sgn[0];
        a.text(sgn);
        a.click(cb);
        li.append(a);
        $("#sgnsbutton").append(li);
    }
    return sgns.length != 0 ? sgns[0][0] : null;
}

function update(data) {
    maindata = data;
    var first = populate_signatures(data);
    if (first != null) {
        $("#signaturestitle").text(first);
        make_tables(first, data[first]);
    } else {
        $("#signaturestitle").text("No signatures !");
        $("#main").empty();
    }
}

function dp_cb(d, p) {
    var loc = window.location;
    var url = loc.protocol + loc.pathname + '?date=' + d + '&product=' + p;
    window.location.href = url;
}

function populate_products(data) {
    var cb = function (e) { dp_cb(curdate, e.target.text); return true; };
    $("#productstitle").text(product);
    $("#productsbutton").empty();
    for (let prod of data.products) {
        let li = $("<li></li>"),
            a = $("<a href=\'#\'></a>");
        a.text(prod);
        a.click(cb);
        li.append(a);
        $("#productsbutton").append(li);
    }
}

function populate_dates(data) {
    var cb = function (e) { dp_cb(e.target.text, product); return true; },
        dates = data.dates;
    curdate = curdate == "" ? dates[0] : curdate;
    $("#datesbutton").empty();
    for (let date of dates) {
        let li = $("<li></li>"),
            a = $("<a href=\'#\'></a>");
        a.text(date);
        a.click(cb);
        li.append(a);
        $("#datesbutton").append(li);
    }
}

function init_patches(prod, chan, date) {
    product = prod;
    curdate = date;
    curchan = chan;
    populate_products(infos);
    populate_dates(infos);
    make_title();
    $("#datestitle").text(curdate);
    $.get("rest/patches",
          {"channel": curchan, "product": product, "date": curdate},
          update, "json");

}
