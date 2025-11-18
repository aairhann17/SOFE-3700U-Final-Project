<!DOCTYPE html>
<html>
<head>
	<title>Sign In - Art Museum</title>
	<link rel="stylesheet" href="../static/css/style.css">
</head>
<body>
<?php
	require("user.php");
	session_start();
	
	$db = new PDO('mysql:host=localhost;dbname=art_museum_db', 'root', 'softEng@2028');
	$db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
	$user = new Users($db);

	if (isset($_SESSION['error'])) {
		echo "<p style='color: red;'>Wrong username or password!</p>";
	}

	if (isset($_POST['username']) && isset($_POST['password'])) {
		$userID = $user->authenticate($_POST['username'], $_POST['password']);
				
		if ($userID) {
			$user->signin($userID);
			$_SESSION['error'] = null;
			// Redirect to Flask museum app
			header("Location: http://localhost:5000/");
			exit;
		}
		else {
			$_SESSION['error'] = true;
			header("Refresh:0");
			exit;
		}
	}
		
	if (isset($_POST['logout'])) {
		$user->logout();
		header("Refresh:0");
		exit;
	}

	$userID = $user->getLoggedInUser();
	
	if ($userID) {
		// User is already logged in, redirect to museum
		header("Location: http://localhost:5000/");
		exit;
	}
?>

<div class="container" style="max-width: 400px; margin: 100px auto;">
	<h1>Art Museum - Sign In</h1>
	<form method="post" action="">
		<div class="form-group">
			<label>Username:</label>
			<input type="text" name="username" class="form-control" maxlength="32" required>
		</div>
		<div class="form-group">
			<label>Password:</label>
			<input type="password" name="password" class="form-control" required>
		</div>
		<button type="submit" class="btn btn-primary">Sign In</button>
	</form>
	<p style="margin-top: 20px;">
		Don't have an account? <a href="create_account.php">Create Account</a>
	</p>
</div>

</body>
</html>
