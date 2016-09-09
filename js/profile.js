var $search_items = $("#search_items")

function searchComments( user ) {

    $.ajax({
        url: "/comments",
        type: "GET",
        dataType: 'json',
        data : {"action": "getCommentsUser", "user": user }

    }).done( function(comments) {
        if (comments){
            $("#main").children().remove();

            for (var i = comments.length - 1; i >= 0; i--) {

                $search_items.append("<li class='search_item'>\
                                        <a href='/post"+comments[i][1].title+"'><h3>"+comments[i][1].title.slice(1).replace(/_/g, " ") +"</h3></a>\
                                        <small class='user_name'>(commented on "+comments[i][1].created+")</small>\
                                    </li>" );
           }
        }
    }).fail(function(e) {
        console.log("e: "+ e);
    });
}