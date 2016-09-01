
function loadData() {
    if( $("input:first").val().length > 0) {

        main = $("#main").clone();

        var query = $("input:first").val().replace(/ /g, "_");
        var $search_items = $("#search_items");

        $search_items.children().remove();

        var RequeestTimeout = setTimeout(function() {
            $("input:first").text("Failed to get resources.");
        }, 5000);

        $.ajax({
            url: "/search/"+query,
            type: "POST",
            dataType: 'json'

        }).done(function(data) {
            if ( data ){

                $("#main").children().remove();

                $.each( data, function( key, val ) {
                    $search_items.append("<li class='search_item'>\
                                            <a href=/post"+ val.title +"><h3>"+ val.title.slice(1).replace(/_/g, " ") +"</h3></a>\
                                            <p>"+ val.content +"</p>\
                                            <small class='user_name'>(by "+ val.user +" on "+ val.modified +")</small>\
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

var main = null;

$("#search_input").keydown( function() {
    if ($("#search_input").val() == "" && $("#main").children().length == 0 ){
        main.clone().appendTo( $("#main") );
        $("#search_items").children().remove();
    }
});


$('#search-form').submit( loadData );

$( document ).ready( function () {
    if( $("input:first").val() != ""){
        loadData();
    };
})
