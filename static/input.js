function Requests(server_data){
    $.ajax({
        type: "POST",
        url: "/process",
        data: JSON.stringify(server_data),
        contentType: "application/json",
        dataType: 'json',
        success: function(data) {
            window.location.reload();
         },
      });
}

function buttonEvent(data){
    Requests(data);
}