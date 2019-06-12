
public class MyClass {
	public static void main(String[] args) {
		int ur = Time.ur();
		boolean peak;
		System.out.println(ur);
		int tempContainer, tempDesired, Sair, Rair;
		tempContainer = -30;
		
		// Initialisering af binær streng, der svarer til den ønskede ændring med henhold til ISO. 
    	String tempISO, SairISO, RairISO;
    	
    	//Sætter peak til true når festivalen bruger diesel-genratorer.  
    	if (ur > 12 && ur < 24) {
    		peak = true; }
    	else {
    		peak = false;
	 					 }
    	
	// Bestemmer hvornår setpoint og luftstrømning skal ændres.  
		if(tempContainer >= -20 || peak) {
			tempDesired = -20;
			Sair = -25;
			Rair = -25;
			tempISO = ISOstring(tempDesired);
			SairISO = "0" + ISOstring(Sair);
	    	RairISO = "0" + ISOstring(Rair);
		}
		else if (tempContainer <= -29) {
			tempDesired = -30;
			Sair = -25;
			Rair = -25;
			tempISO = "0" + ISOstring(tempDesired);
			SairISO = "0" + ISOstring(Sair);
	    	RairISO = "0" + ISOstring(Rair);
		}
		else {
			tempDesired = -30;
			Sair = 75;
			Rair = 75; 
			tempISO = "0" + ISOstring(tempDesired);
			SairISO = ISOstring(Sair);
			RairISO = ISOstring(Rair);
		}
		
		
	// Alarm string, 100 angiver standard alarm 
		String alarm = "100";
	// Recent defrost R 
		String R = "0";
	// Mode, idk what it is 	
		String Mode = "1111";
	// Alarm flags, 20 bits der er alle er 0 hvis intet er galt 
		String flags = "00000000000000000000";
	// Den smalede string der sendes til containeren 
		String bitstreng = flags + alarm + Mode + RairISO + SairISO + tempISO;
		System.out.println(bitstreng); 
	}
		
	
	
	public static String ISOstring(int tempair) {
		//Returnerer binær streng i overenstemmelse med ISO 
		double tempISOdouble = (125 + tempair)/0.05;
		int tempISO = (int) Math.round(tempISOdouble);
		return Integer.toBinaryString(tempISO);
	}
}

