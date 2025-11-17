<!DOCTYPE html>
<html>
<head>
    <title>Sign In - Art Museum</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
        .login-card { background: white; border-radius: 15px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); padding: 40px; max-width: 400px; width: 100%; }
        .login-card h1 { color: #667eea; margin-bottom: 30px; }
    </style>
</head>
<body>
<?php
    require("user.php");
    session_start();
    
    $db = new PDO('mysql:host=localhost;dbname=art_museum_db', 'root', 'softEng@2028');
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $user = new Users($db);

    if (isset($_POST['username']) && isset($_POST['password'])) {
        $userID = $user->authenticate($_POST['username'], $_POST['password']);
                
        if ($userID) {
            $user->signin($userID);
            
            // Get user role from database
            $stmt = $db->prepare("SELECT role FROM user WHERE ID = :id");
            $stmt->execute(['id' => $userID]);
            $userRole = $stmt->fetchColumn();
            $_SESSION['userRole'] = $userRole;
            $_SESSION['error'] = null;
            
            // Redirect to Flask login callback with user ID
            header("Location: http://localhost:5000/auth/callback?user_id=" . $userID);
            exit;
        }
        else {
            $_SESSION['error'] = true;
            header("Refresh:0");
            exit;
        }
    }
        
    $userID = $user->getLoggedInUser();
    
    if ($userID) {
        // User is already logged in, redirect to callback
        header("Location: http://localhost:5000/auth/callback?user_id=" . $userID);
        exit;
    }
?>

<div class="login-card">
    <h1><i class="fas fa-palette"></i> Art Museum</h1>
    <?php if (isset($_SESSION['error'])): ?>
        <div class="alert alert-danger"><i class="fas fa-exclamation-circle"></i> Wrong username or password!</div>
        <?php $_SESSION['error'] = null; ?>
    <?php endif; ?>
    <form method="post" action="">
        <div class="mb-3">
            <label class="form-label">Username</label>
            <input type="text" name="username" class="form-control" maxlength="32" required autofocus>
        </div>
        <div class="mb-3">
            <label class="form-label">Password</label>
            <input type="password" name="password" class="form-control" required>
        </div>
        <button type="submit" class="btn btn-primary w-100"><i class="fas fa-sign-in-alt"></i> Sign In</button>
    </form>
    <hr>
    <div class="text-center"><p class="mb-0">Don't have an account? <a href="create_account.php">Create Account</a></p></div>
</div>

</body>
</html>
