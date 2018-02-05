$(document).ready(function () {
	let socket = io.connect(location.protocol + "//" + document.domain + ":" + location.port);
	socket.emit("connect", {"cookie":getCookie("session_id")});

	socket.on("joined",function (msg) {
		showdiv("startwait")
	});

	

	socket.on("userlist",function (msg) {

	});

	setInterval(function () {
		socket.emit("ping", {"cookie":getCookie("session_id")})
	}, (20 * 1000));

	showdiv("nicknameinput")
});

function showdiv(divid) {
	$(".container").hide()
	$(".container#"+divid).show()
}


function getCookie(cname) {
	var name = cname + "=";
	var ca = document.cookie.split(";");
	for(var i = 0; i <ca.length; i++) {
		var c = ca[i];
		while (c.charAt(0)==" ") {
			c = c.substring(1);
		}
		if (c.indexOf(name) == 0) {
			return c.substring(name.length,c.length);
		}
	}
	return "";
}
