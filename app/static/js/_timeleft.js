$(document).ready(function(){

    $('.timeleft .timestamp').each(function(i, elem){
        var $elem = $(elem);
        setTimeout(function(){
            $elem.text(moment($elem.data('timestamp')).fromNow());
        }, 1000);
    });

});
