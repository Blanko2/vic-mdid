<?php
/**
* Wrapper of ObjectSearch.php which returns a json object
*/
include '../../../../setup.php';
include 'ObjectSearch.php';
include 'ca_objects.php';

$sterm = $_GET['q'];
$start = $_GET['start'];
$end = $_GET['end'];
$get = $_GET['get'];
if ($start == NULL)
    $start = 0;
if ($get != NULL){
    $search_results = new ca_objects($get);
    $end = 1;
    print "{";
    #print "\\\""."artist"."\\\":\\\"".$search_results->get('ca_entities', array('delimiter' => ';', 'restrictToRelationshipTypes' => 'artist'))."\\\", <br>";
    #print "\\\""."artist"."\\\":\\\"".$search_results->get('ca_entities', array('delimiter' => ';', 'convertCodesToDisplayText' => true))."\\\", <br>";
    print "\\\""."Title(s)"."\\\":\\\"".$search_results->get('ca_objects.preferred_labels.name')."\\\", <br>";
    print "\\\""."description"."\\\":\\\"".$search_results->get('ca_objects.work_description')."\\\", <br>";
    print "\\\""."media"."\\\":\\\"".$search_results->get('ca_objects.work_medium')."\\\", <br>";
    print "\\\""."Measurements"."\\\":\\\"".$search_results->get('ca_objects.work_dimensions', array('convertCodesToDisplayText' => true))."\\\", <br>";
    print "\\\""."work_date"."\\\":\\\"".$search_results->get('ca_objects.work_date')."\\\", <br>";
    print "\\\""."Creation Date"."\\\":\\\"".$search_results->get("ca_objects.date", array('delimiter' => ': ', 'convertCodesToDisplayText' => true))."\\\", <br>";
    print "\\\""."Creator(s)"."\\\":\\\"".$search_results->get('ca_objects_x_entities.type', array('delimiter' => '; ', 'convertCodesToDisplayText' => true))."\\\", <br>";
    //print "\\\"".""."\\\":\\\"".""."\\\", <br>";
    //print "\\\"".""."\\\":\\\"".""."\\\", <br>";
    //print "\\\"".""."\\\":\\\"".""."\\\", <br>";
    //print "\\\"".""."\\\":\\\"".""."\\\", <br>";
    //print "\\\"".""."\\\":\\\"".""."\\\", <br>";
    print "}fdsh";
    }
else{
    $searcher = new ObjectSearch();
    //Apparently CA uses Lucene syntax to form queries, should exploit that for advanced search
    $search_results = $searcher->search($sterm, null);
    $count = 0;
    $result = array();
    while($search_results->nextHit()) {

        $result[] = "{\\\"name\\\" : \\\"".$search_results->get('ca_objects.preferred_labels.name')."\\\", \\\"url\\\" : \\\"".$search_results->getMediaUrl('ca_object_representations.media', "original")."\\\", \\\"thumb\\\" : \\\"".$search_results->getMediaUrl('ca_object_representations.media', "thumbnail")."\\\", \\\"idno\\\" : \\\"".$search_results->get('idno')."\\\", \\\"artist\\\" : \\\"".$search_results->get('ca_entities', array('delimiter' => '; ', 'restrictToRelationshipTypes' => 'artist'))."\\\", \\\"description\\\" : \\\"".$search_results->get('ca_objects.description')."\\\", \\\"id\\\" : \\\"".$search_results->get('ca_objects.object_id')."\\\"}";
        $count++;
        //print $search_results->get("ca_object_labels.name_sort");
        //print "Hit ".$count.": ".$search_results->get('ca_objects.preferred_labels.name')."<br/>\n";
        //print "url: ".$search_results->getMediaUrl('ca_object_representations.media', "original")."<br/>\n";
        //print "path: ".$search_results->getMediaPath('ca_object_representations.media', "original")."<br/>\n";
    }
    $i = $start;
    if ($end == NULL || $end >= $count)
        $end = $count;
    //maybe use .numHits() and .seek($index)
    //also interesting currentIndes() and previousHit()
    //getFieldInfo($field), getMediaInfo, hasMedia($field) getFileInfo($ps_field)  hasFile($ps_field)  getDate($ps_field, $pa_options=null)
    //print "Start = ".$start.", end = ".$end."<br>";
    print $count."{";
    $comma = "";
    while ($i < $end){
        print $comma."\"".$i."\" : \"".$result[$i]."\"" ;
        $i++;
        $comma = ", ";
    }
    print "}";
}
//print "Found <b>".$count."</b> result(s)"
/**

    /* Get data from ObjectSearch->&search($ps_search, $pa_options), format to
	[{name: "name", thumb: "thumb_url", url: "url", creator: "creator", anything else useful}, record2, record3...] or similar

    

    json_encode and return */



?>