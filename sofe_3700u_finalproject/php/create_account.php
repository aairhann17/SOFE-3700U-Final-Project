<!DOCTYPE html>
<html>
<head>
	<title>Create Account - Art Museum</title>
	<link rel="stylesheet" href="../static/css/style.css">
</head>
<body>
<?php
	require("user.php");
	session_start();
	
	$db = new PDO('mysql:host=localhost;dbname=art_museum_db', 'root', 'softEng@2028');
	$db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
	$user = new Users($db);

	$error_message = '';
	
	if (isset($_SESSION['email_error'])) {
		$error_message = "Invalid email!";
		$_SESSION['email_error'] = null;
	}
	
	if (isset($_SESSION['username_error'])) {
		$error_message = "Username already exists!";
		$_SESSION['username_error'] = null;
	}
	
	if (isset($_POST['email']) && isset($_POST['create_username']) && isset($_POST['create_password'])) {
		$sanitized_email = filter_var($_POST['email'], FILTER_SANITIZE_EMAIL);
		if (!filter_var($sanitized_email, FILTER_VALIDATE_EMAIL)) {
			$_SESSION['email_error'] = true;
			header("Refresh:0");
			exit;
		}
		
		$user_created = $user->createUser($sanitized_email, $_POST['create_username'], $_POST['create_password'], intval(0));
		if ($user_created == 0) {
			$db = null;
			header("Location: signin.php");
			exit;
		}
		
		else if ($user_created == 1) {
			$_SESSION['email_error'] = true;
			header("Refresh:0");
			exit;
		}
		
		else if ($user_created == 2) {
			$_SESSION['username_error'] = true;
			header("Refresh:0");
			exit;
		}
	}
?>

<div class="container" style="max-width: 400px; margin: 100px auto;">
	<h1>Create Account</h1>
	
	<?php if ($error_message): ?>
		<p style="color: red;"><?php echo $error_message; ?></p>
	<?php endif; ?>
	
	<form method="post" action="">
		<div class="form-group">
			<label>Email:</label>
			<input type="text" name="email" class="form-control" maxlength="64" required>
		</div>
		<div class="form-group">
			<label>Username:</label>
			<input type="text" name="create_username" class="form-control" maxlength="32" required>
		</div>
		<div class="form-group">
			<label>Password:</label>
			<input type="password" name="create_password" class="form-control" maxlength="64" required>
		</div>
		<button type="submit" class="btn btn-primary">Create Account</button>
	</form>
	<p style="margin-top: 20px;">
		Already have an account? <a href="signin.php">Sign In</a>
	</p>
</div>

</body>
</html>

