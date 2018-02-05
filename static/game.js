currentquestion = -1;

answerone = -1;
answertwo = -1;

$(document).ready(function () {
	let socket = io.connect(location.protocol + "//" + document.domain + ":" + location.port);
	socket.emit("connected", {"cookie":getCookie("session_id")});

	socket.on("joined",function (msg) {
		showdiv("startwait");
		$("#mynickname").html(msg.nickname);
	});

	socket.on("timerupdate",function (msg) {
		$("#countdown").html(msg.time);
	});

	socket.on("loading",function (msg) {
		showdiv("loading");
	});

	socket.on("ready",function (msg) {
		socket.emit("ready",{"cookie":getCookie("session_id")});
	});

	socket.on("question",function (msg) {
		showdiv("questioninput");
		$("#question").html(msg.question);
		currentquestion = msg.qid;
		$("#answer").val("");
	});

	socket.on("userlist",function (msg) {
		var users = "";
		for (i=0; i < msg.users.length; i++) {
			users += msg.users[i] + "<br>";
		}
		$("#playerlist").html(users);
		if (msg.canstart) {
			$("#startgame").show();
		}
	});

	socket.on("holdon",function (msg) {
		showdiv("waiting");
	});

	setInterval(function () {
		socket.emit("ping", {"cookie":getCookie("session_id")});
	}, (20 * 1000));

	$("#submitnick").on("click", function( event ) {
		var nick = $("#nick").val();
		socket.emit("join",{"cookie":getCookie("session_id"),"nickname":nick});
	});

	$("#startgame").on("click", function( event ) {
		socket.emit("start");
	});

	$("#submitanswer").on("click", function( event ) {
		showdiv("waiting");
		socket.emit("answer",{"cookie":getCookie("session_id"),"qid":currentquestion,"answer":$("#answer").val()});
	});

	$("#startgame").hide();

	showdiv("nicknameinput");
});

function showdiv(divid) {
	$(".container").hide();
	$("#"+divid).show();
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
