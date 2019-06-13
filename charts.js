@Override
@Transactional
public JSONArray createcsv_year(String year) throws FileNotFoundException
{
   // TODO Auto-generated method stub
    Session currentSession = sessionFactory.getCurrentSession();



     // create a query
Query<Device_Status> theQuery1 = currentSession.createQuery("from Device_Status", Device_Status.class);

  // execute query and get result list
List<Device_Status> devicestatus = theQuery1.getResultList();


int devicesize=devicestatus.size();
     int[] device_id=new int[devicesize];
int[] count=new int[devicesize];
double[] avg_temperature=new double[devicesize];
double[] avg_humidity=new double[devicesize];
StringBuilder[] sb=new StringBuilder[devicesize];

for(int i=0;i<devicesize;i++)
{
  device_id[i]=devicestatus.get(i).getDeviceid();
  count[i]=0;
  avg_temperature[i]=0;
  avg_humidity[i]=0;
  sb[i]=new StringBuilder("");
}


     int year1=Integer.parseInt(year);

    for(int i=1;i<=12;i++)
    {

    YearMonth yearMonthObject = YearMonth.of(year1, i);
    int daysInMonth = yearMonthObject.lengthOfMonth();


    LocalDate st1 = LocalDate.of(year1,i,1);

LocalDate ed1= LocalDate.of(year1,i,daysInMonth);


// create a query
Query<DeviceDate> theQuery = currentSession.createQuery("from DeviceDate where date BETWEEN '"+st1+"' AND '"+ed1+"' ", DeviceDate.class);

// execute query and get result list
List<DeviceDate> deviceDate = theQuery.getResultList();

for(DeviceDate date: deviceDate)
{
    List<DeviceDetails> deviceDetails= (List<DeviceDetails>) date.getDeviceDetails();

    for(DeviceDetails dd: deviceDetails)
  {
    for(int index=0;index<devicesize;index++)
   {
   if(dd.getDevice_id()==device_id[index])
   {


   avg_temperature[index]+=Double.valueOf(dd.getTemperature());
   avg_humidity[index]+=Double.valueOf(dd.getHumidity());
   count[index]+=1;
   }

   }


}
}



   for(int index=0;index<devicesize;index++)
   {
                       Double temperature=avg_temperature[index]/count[index];
                       Double humidity=avg_humidity[index]/count[index];

                       if(Double.isNaN(temperature) || Double.isInfinite(temperature))
                       {
                       temperature=0.0;
                       }
                       if(Double.isNaN(humidity) || Double.isInfinite(humidity))
                       {
                       humidity=0.0;
                       }

                       JSONObject jsonobj=new  JSONObject();

                       try
                       {

       jsonobj.put("DeviceId",String.valueOf(device_id[index]));
       jsonobj.put("Humidity",humidity.toString());
                           jsonobj.put("Temperature",temperature.toString());
                           jsonobj.put("Date",String.valueOf(i));
       }
                       catch (JSONException e)
                       {

    e.printStackTrace();
       }


                          if(i==12)
                           sb[index].append(jsonobj.toString());
                          else
                           sb[index].append(jsonobj.toString()+",");




   count[index]=0;
   avg_temperature[index]=0;
   avg_humidity[index]=0;



   }


     }

       Jsonwritedata obj=new Jsonwritedata();
       JSONArray jsondata=obj.responcedata_week(devicesize,sb);
       return jsondata;
}
