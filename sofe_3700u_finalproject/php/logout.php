<?php
	session_start();
	session_regenerate_id(true);
	$_SESSION["loggedInUser"] = null;
	header("Location: signin.php");
	exit;
?>
