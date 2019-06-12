
import java.time.*; 
  
// create class 
public class Time{ 
  
    // Main method 
   public static int ur()
    { 
  
        // create a Zone Id for Europe/Paris 
        ZoneId zoneId = ZoneId.of("Europe/Paris"); 
  
        // create Clock with system(zoneId) method 
        Clock clock = Clock.system(zoneId); 
  
        // get instant of class 
        Instant instant = clock.instant(); 
  
        // get ZonedDateTime object from instantObj to get date time 
        ZonedDateTime time = instant.atZone(clock.getZone()); 
  
        // print details of time  
        String s = time.toString();
        String s2 = s.substring(11,13);
     
        int result = Integer.parseInt(s2);
        return result;
    } 
} 




