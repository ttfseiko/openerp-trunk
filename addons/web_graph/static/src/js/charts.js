
openerp.web_graph.draw_chart = function (mode, pivot, svg) {
    openerp.web_graph[mode](pivot, svg);
};


openerp.web_graph.bar_chart = function (pivot, svg) {
    var dim_x = pivot.rows.groupby.length,
        dim_y = pivot.cols.groupby.length,
        data = [];

    // No groupby **************************************************************
    if ((dim_x === 0) && (dim_y === 0)) {
        data = [{key: 'Total', values:[{
            title: 'Total',
            value: pivot.get_value(pivot.rows.main.id, pivot.cols.main.id),
        }]}];
        nv.addGraph(function () {
          var chart = nv.models.discreteBarChart()
                .x(function(d) { return d.title;})
                .y(function(d) { return d.value;})
                .tooltips(false)
                .showValues(true)
                .staggerLabels(true)
                .width(650)
                .height(400);

            d3.select(svg)
                .datum(data)
                .attr('width', 650)
                .attr('height', 400)
                .call(chart);

            nv.utils.windowResize(chart.update);
            return chart;
        });
    // Only column groupbys ****************************************************
    } else if ((dim_x === 0) && (dim_y >= 1)){
        _.each(pivot.cols.headers, function (header) {
            if (header.path.length === 1) {
                data.push({
                    key: header.title,
                    values: [{x:header.root.main.title, y: pivot.get_total(header)}]
                });
            }
        });
        nv.addGraph(function() {
            var chart = nv.models.multiBarChart()
                    .stacked(true)
                    .tooltips(false)
                    .showControls(false)
                    .width(400)
                    .height(500);

            d3.select(svg)
                .datum(data)
                .attr('width', 400)
                .attr('height', 500)
                .transition()
                .duration(500)
                .call(chart);

            nv.utils.windowResize(chart.update);

            return chart;
        });
    // Just 1 row groupby ******************************************************
    } else if ((dim_x === 1) && (dim_y === 0))  {
        data = _.map(pivot.rows.main.children, function (pt) {
            var value = pivot.get_value(pt.id, pivot.cols.main.id),
                title = (pt.title !== undefined) ? pt.title : 'Undefined';
            return {title: title, value: value};
        });
        data = [{key: 'Bar chart', values:data}];
        nv.addGraph(function () {
          var chart = nv.models.discreteBarChart()
                .x(function(d) { return d.title;})
                .y(function(d) { return d.value;})
                .tooltips(false)
                .showValues(true)
                .staggerLabels(true)
                .width(650)
                .height(400);

            d3.select(svg)
                .datum(data)
                .attr('width', 650)
                .attr('height', 400)
                .call(chart);

            nv.utils.windowResize(chart.update);
            return chart;
        });
    // 1 row groupby and some col groupbys**************************************
    } else if ((dim_x === 1) && (dim_y >= 1))  {
        data = [];
        _.each(pivot.cols.headers, function (colhdr) {
            if (colhdr.path.length === 1) {
                var values = [];
                _.each(pivot.rows.headers, function (header) {
                    if (header.path.length === 1) {
                        values.push({
                            x: header.title || 'Undefined',
                            y: pivot.get_value(header.id, colhdr.id, 0)
                        });
                    }
                });
                data.push({key: colhdr.title || 'Undefined', values: values});
            }
        });

        nv.addGraph(function () {
          var chart = nv.models.multiBarChart()
                .stacked(true)
                .staggerLabels(true)
                .tooltips(false)
                .width(650)
                .height(400);

            d3.select(svg)
                .datum(data)
                .attr('width', 650)
                .attr('height', 400)
                .call(chart);

            nv.utils.windowResize(chart.update);
            return chart;
        });
    // At least two row groupby*************************************************
    } else {
        data = [];
        var keys = _.uniq(_.map(_.filter(pivot.rows.headers, function (hdr) {
            return hdr.path.length === 2;
        }), function (hdr) {
            return hdr.title || 'Undefined';
        }));
        data = _.map(keys, function (key) {
            var values = [];
            _.each(pivot.rows.headers, function (hdr) {
                if (hdr.path.length === 1) {
                    var subhdr = _.find(hdr.children, function (child) {
                        return ((child.title === key) || ((child.title === undefined) && (key === 'Undefined')));
                    });
                    values.push({
                        x: hdr.title || 'Undefined', 
                        y: (subhdr) ? pivot.get_total(subhdr) : 0
                    });
                }
            });

            return {key:key, values: values};
        });

        nv.addGraph(function () {
          var chart = nv.models.multiBarChart()
                .stacked(true)
                .staggerLabels(true)
                .tooltips(false)
                .transitionDuration(0)
                .width(650)
                .height(400);

            d3.select(svg)
                .datum(data)
                .attr('width', 650)
                .attr('height', 400)
                .call(chart);
                debugger;

            nv.utils.windowResize(chart.update);
            return chart;
        });
    }
};


openerp.web_graph.line_chart = function (pivot, svg) {
    var data = _.map(pivot.rows.main.children, function (pt) {
    var value = pivot.get_value(pt.id, pivot.cols.main.id),
        title = (pt.title !== undefined) ? pt.title : 'Undefined';
            return {x: title, y: value};
        });

    nv.addGraph(function () {
        var chart = nv.models.lineChart()
            .x(function (d,u) { return u; })
            .width(600)
            .height(300)
            .margin({top: 30, right: 20, bottom: 20, left: 60});

        d3.select(svg)
            .attr('width', 600)
            .attr('height', 300)
            .datum([{key: 'Bar chart', values: data}])
            .call(chart);

        return chart;
      });
};

openerp.web_graph.pie_chart = function (pivot, svg) {
    var data = _.map(pivot.rows.main.children, function (pt) {
        var value = pivot.get_value(pt.id, pivot.cols.main.id),
            title = (pt.title !== undefined) ? pt.title : 'Undefined';
        return {x: title, y: value};
    });
    
    nv.addGraph(function () {
        var chart = nv.models.pieChart()
            .color(d3.scale.category10().range())
            .width(650)
            .height(400);

        d3.select(svg)
            .datum(data)
            .transition().duration(1200)
            .attr('width', 650)
            .attr('height', 400)
            .call(chart);

        nv.utils.windowResize(chart.update);
        return chart;
    });
};
