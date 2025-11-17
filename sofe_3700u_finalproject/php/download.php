<?php
	$dbusername = "root";
	$dbpassword = "1234";
			
	$db = new PDO('mysql:host=localhost;dbname=gallery', $dbusername, $dbpassword);
			
	$db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
	
	if (!$db) {
		echo "Error connecting to database";
		exit;
	}
	
	if (isset($_POST["download"])) {
		if (!isset($_POST["tables"])) {
			exit;
		}
		
		$selected_table = $_POST["tables"]; //get selected button
		
		//get data from respective tables
		if ($selected_table == "artist") {
			$stmt = $db->prepare("SELECT * FROM artist");
			$stmt->execute();
			$table = $stmt->fetchAll(PDO::FETCH_ASSOC);
			$filename = "artist.csv";
		}
		
		else if ($selected_table == "object_details") {
			$stmt = $db->prepare("SELECT * FROM objectdetails");
			$stmt->execute();
			$table = $stmt->fetchAll(PDO::FETCH_ASSOC);
			$filename = "object_details.csv";
		}
		
		else if ($selected_table == "object_gallery") {
			$stmt = $db->prepare("SELECT * FROM objectgallerydata");
			$stmt->execute();
			$table = $stmt->fetchAll(PDO::FETCH_ASSOC);
			$filename = "object_gallery_data.csv";
		}
		
		else if ($selected_table == "object_origins") {
			$stmt = $db->prepare("SELECT * FROM objectorigins");
			$stmt->execute();
			$table = $stmt->fetchAll(PDO::FETCH_ASSOC);
			$filename = "object_origins.csv";
		}
		
		$file = fopen($filename, "w+"); //open a new file with write permissions
		$columns = array_keys(current($table)); //write columns to file
		
		fputcsv($file, $columns, ","); //format csv file with "," as delimiter
		
		foreach ($table as $data) { //add each row to file
			fputcsv($file, $data, ",");
		}	
		
		fseek($file, 0); //set file pointer to start
		
		//download file
		header('Content-Type: text/csv');
		header('Content-Disposition: attachment; filename="' .$filename . '";');
		
		fpassthru($file);
		fclose($file);
	}
	exit;

?>

<form method="post" action="download.php">
	<input type="radio" id="artist" name="tables" value="artist" checked> Artist<br>
	<input type="radio" id="object_details" name="tables" value="object_details"> Object Details<br>
	<input type="radio" id="object_gallery" name="tables" value="object_gallery"> Object Gallery Details<br>
	<input type="radio" id="object_origins" name="tables" value="object_origins"> Object Origins<br><br>
	<input type="submit" name="download" value="Download Table"><br><br>
</form>
