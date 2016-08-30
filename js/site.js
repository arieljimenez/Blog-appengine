
function loadData() {
    if( $("input:first").val().length > 0) {
        ranking =  $("#ranking").clone();

        var query = $("input:first").val();
        var $main = $("#main");
        var $search_items = $("#search_items");

        $("#ranking").children().remove();
        $search_items.children().remove();

        var RequeestTimeout = setTimeout(function() {
            $("input").text("Failed to get resources.");
        }, 5000);

        $.ajax({
            url: "/search/"+query,
            type: "POST",
            dataType: 'json'

        }).done(function(data) {
            if ( data ){
                $.each( data, function( key, val ) {
                    $search_items.append("<li class='search_item'>\
                                            <a href=/post"+ val.title +"><h3>"+ val.title.slice(1).replace(/_/g, " ") +"</h3></a>\
                                            <span>"+ val.content +"</span>\
                                            <small>(by "+ val.user +")</small>\
                                         </li>" );
                });

            } else {
                 $search_items.append( "<li class='error'> No post found. Try again with another word.</li>" );
            }

            clearTimeout(RequeestTimeout);

        }).fail(function(e) {
            console.log("e: "+ e);
        });
    };

    return false;

};

var ranking =  null;

$("#search_input").keydown( function() {
    if ($("#search_input").val() == "" && $("#ranking").children().length == 0 ){
        ranking.clone().appendTo($("#ranking"));
        $("#search_items").children().remove();
    }

});


$('#search-form').submit( loadData );
