
/* File generated by gen_cfile.py. Should not be modified. */

#include "jsontest_legacy.h"

/**************************************************************************/
/* Declaration of mapped variables                                        */
/**************************************************************************/
UNS8 VAR = 0x0;		/* Mapped at index 0x2000, subindex 0x00 */
INTEGER8 ARRAY[] =		/* Mapped at index 0x2001, subindex 0x01 - 0x02 */
  {
    0x1,	/* 1 */
    0x2	/* 2 */
  };
UNS8 RECORD_RECORD_1 = 0x7;		/* Mapped at index 0x2002, subindex 0x01 */
INTEGER16 RECORD_RECORD_2 = 0x2A;		/* Mapped at index 0x2002, subindex 0x02 */
UNS8 Global_Interrupt_Enable_Digital_Sure = 0x0;		/* Mapped at index 0x6000, subindex 0x00 */
INTEGER32 RECORD_Software_position_limit_Minimal_position_limit = 0x1;		/* Mapped at index 0x6100, subindex 0x01 */
INTEGER32 RECORD_Software_position_limit_Maximal_position_limit = 0x2;		/* Mapped at index 0x6100, subindex 0x02 */
INTEGER16 RECORD_AL_Action_AL_1_Action_1 = 0x1;		/* Mapped at index 0x6180, subindex 0x01 */
INTEGER16 RECORD_AL_Action_AL_1_Action_2 = 0x2;		/* Mapped at index 0x6180, subindex 0x02 */
INTEGER16 RECORD_AL_Action_AL_1_Action_3 = 0x3;		/* Mapped at index 0x6180, subindex 0x03 */
INTEGER16 RECORD_AL_Action_AL_1_Action_4 = 0x4;		/* Mapped at index 0x6180, subindex 0x04 */
INTEGER16 RECORD_AL_Action_AL_1_Action_5 = 0x5;		/* Mapped at index 0x6180, subindex 0x05 */
INTEGER16 RECORD_AL_Action_AL_1_Action_6 = 0x6;		/* Mapped at index 0x6180, subindex 0x06 */
INTEGER16 ARRAY_Acceleration_Value[] =		/* Mapped at index 0x6200, subindex 0x01 - 0x02 */
  {
    0x1,	/* 1 */
    0x10	/* 16 */
  };
UNS32 Device_Type_1_and_0 = 0x1;		/* Mapped at index 0x6300, subindex 0x00 */
UNS32 Device_Type_2_and_0 = 0xC;		/* Mapped at index 0x6302, subindex 0x00 */
INTEGER32 NARRAY_CAM1_Low_Limit[] =		/* Mapped at index 0x6400, subindex 0x01 - 0x02 */
  {
    0x1,	/* 1 */
    0x2	/* 2 */
  };
INTEGER32 NARRAY_CAM2_Low_Limit[] =		/* Mapped at index 0x6402, subindex 0x01 - 0x00 */
  {
  };
UNS32 NRECORD_Receive_PDO_1_Parameter_COB_ID_used_by_PDO = 0x1;		/* Mapped at index 0x6500, subindex 0x01 */
UNS8 NRECORD_Receive_PDO_1_Parameter_Transmission_Type = 0x2;		/* Mapped at index 0x6500, subindex 0x02 */
UNS16 NRECORD_Receive_PDO_1_Parameter_Inhibit_Time = 0x3;		/* Mapped at index 0x6500, subindex 0x03 */
UNS8 NRECORD_Receive_PDO_1_Parameter_Compatibility_Entry = 0x4;		/* Mapped at index 0x6500, subindex 0x04 */
UNS16 NRECORD_Receive_PDO_1_Parameter_Event_Timer = 0x5;		/* Mapped at index 0x6500, subindex 0x05 */
UNS8 NRECORD_Receive_PDO_1_Parameter_SYNC_start_value = 0x6;		/* Mapped at index 0x6500, subindex 0x06 */
UNS32 NRECORD_AL_1_Action_AL_1_Action_1 = 0x1;		/* Mapped at index 0x6580, subindex 0x01 */
UNS32 NRECORD_AL_1_Action_AL_1_Action_2 = 0x2;		/* Mapped at index 0x6580, subindex 0x02 */
UNS32 NRECORD_AL_1_Action_AL_1_Action_3 = 0x3;		/* Mapped at index 0x6580, subindex 0x03 */
UNS32 NRECORD_AL_1_Action_AL_1_Action_4 = 0x4;		/* Mapped at index 0x6580, subindex 0x04 */
UNS32 NRECORD_AL_1_Action_AL_1_Action_5 = 0x5;		/* Mapped at index 0x6580, subindex 0x05 */
UNS32 NRECORD_AL_1_Action_AL_1_Action_6 = 0x6;		/* Mapped at index 0x6580, subindex 0x06 */
UNS16 Producer_Heartbeat_Time = 0x1;		/* Mapped at index 0x6600, subindex 0x00 */

/**************************************************************************/
/* Declaration of value range types                                       */
/**************************************************************************/

#define valueRange_EMC 0x9F /* Type for index 0x1003 subindex 0x00 (only set of value 0 is possible) */
#define valueRange_1 0xA0 /* Type UNS32, 100 < value < 200 */
UNS32 jsontest_valueRangeTest (UNS8 typeValue, void * value)
{
  switch (typeValue) {
    case valueRange_EMC:
      if (*(UNS8*)value != (UNS8)0) return OD_VALUE_RANGE_EXCEEDED;
      break;
    case valueRange_1:
      if (*(UNS32*)value < (UNS32)100) return OD_VALUE_TOO_LOW;
      if (*(UNS32*)value > (UNS32)200) return OD_VALUE_TOO_HIGH;
    break;
  }
  return 0;
}

/**************************************************************************/
/* The node id                                                            */
/**************************************************************************/
/* node_id default value.*/
UNS8 jsontest_bDeviceNodeId = 0x00;

/**************************************************************************/
/* Array of message processing information */

const UNS8 jsontest_iam_a_slave = 0;

TIMER_HANDLE jsontest_heartBeatTimers[1];

/*
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

                               OBJECT DICTIONARY

$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
*/

/* index 0x1000 :   Device Type. */
                    UNS32 jsontest_obj1000 = 0x0;	/* 0 */
                    ODCallback_t jsontest_Index1000_callbacks[] = 
                     {
                       NULL,
                     };
                    subindex jsontest_Index1000[] = 
                     {
                       { RO|TO_BE_SAVE, uint32, sizeof (UNS32), (void*)&jsontest_obj1000 }
                     };

/* index 0x1001 :   Error Register. */
                    UNS8 jsontest_obj1001 = 0x0;	/* 0 */
                    subindex jsontest_Index1001[] = 
                     {
                       { RO|TO_BE_SAVE, uint8, sizeof (UNS8), (void*)&jsontest_obj1001 }
                     };

/* index 0x1003 :   Pre-defined Error Field */
                    UNS8 jsontest_highestSubIndex_obj1003 = 0; /* number of subindex - 1*/
                    UNS32 jsontest_obj1003[] =
                    {
                      0x0	/* 0 */
                    };
                    ODCallback_t jsontest_Index1003_callbacks[] =
                     {
                       NULL,
                       NULL,
                     };
                    subindex jsontest_Index1003[] =
                     {
                       { RW, valueRange_EMC, sizeof (UNS8), (void*)&jsontest_highestSubIndex_obj1003 },
                       { RO, uint32, sizeof (UNS32), (void*)&jsontest_obj1003[0] }
                     };

/* index 0x1005 :   SYNC COB ID */
                    UNS32 jsontest_obj1005 = 0x0;   /* 0 */

/* index 0x1006 :   Communication / Cycle Period */
                    UNS32 jsontest_obj1006 = 0x0;   /* 0 */

/* index 0x100C :   Guard Time */
                    UNS16 jsontest_obj100C = 0x0;   /* 0 */

/* index 0x100D :   Life Time Factor */
                    UNS8 jsontest_obj100D = 0x0;   /* 0 */

/* index 0x1014 :   Emergency COB ID */
                    UNS32 jsontest_obj1014 = 0x80 + 0x00;   /* 128 + NodeID */

/* index 0x1016 :   Consumer Heartbeat Time */
                    UNS8 jsontest_highestSubIndex_obj1016 = 0;
                    UNS32 jsontest_obj1016[]={0};

/* index 0x1017 :   Producer Heartbeat Time */
                    UNS16 jsontest_obj1017 = 0x0;   /* 0 */

/* index 0x1018 :   Identity. */
                    UNS8 jsontest_highestSubIndex_obj1018 = 4; /* number of subindex - 1*/
                    UNS32 jsontest_obj1018_Vendor_ID = 0x0;	/* 0 */
                    UNS32 jsontest_obj1018_Product_Code = 0x0;	/* 0 */
                    UNS32 jsontest_obj1018_Revision_Number = 0x0;	/* 0 */
                    UNS32 jsontest_obj1018_Serial_Number = 0x0;	/* 0 */
                    ODCallback_t jsontest_Index1018_callbacks[] = 
                     {
                       NULL,
                       NULL,
                       NULL,
                       NULL,
                       NULL,
                     };
                    subindex jsontest_Index1018[] = 
                     {
                       { RO|TO_BE_SAVE, uint8, sizeof (UNS8), (void*)&jsontest_highestSubIndex_obj1018 },
                       { RO, uint32, sizeof (UNS32), (void*)&jsontest_obj1018_Vendor_ID },
                       { RO, uint32, sizeof (UNS32), (void*)&jsontest_obj1018_Product_Code },
                       { RO, uint32, sizeof (UNS32), (void*)&jsontest_obj1018_Revision_Number },
                       { RO|TO_BE_SAVE, uint32, sizeof (UNS32), (void*)&jsontest_obj1018_Serial_Number }
                     };

/* index 0x1280 :   Client SDO 1 Parameter. */
                    UNS8 jsontest_highestSubIndex_obj1280 = 3; /* number of subindex - 1*/
                    UNS32 jsontest_obj1280_COB_ID_Client_to_Server_Transmit_SDO = 0x0;	/* 0 */
                    UNS32 jsontest_obj1280_COB_ID_Server_to_Client_Receive_SDO = 0x0;	/* 0 */
                    UNS8 jsontest_obj1280_Node_ID_of_the_SDO_Server = 0x0;	/* 0 */
                    ODCallback_t jsontest_Index1280_callbacks[] = 
                     {
                       NULL,
                       NULL,
                       NULL,
                       NULL,
                     };
                    subindex jsontest_Index1280[] = 
                     {
                       { RO|TO_BE_SAVE, uint8, sizeof (UNS8), (void*)&jsontest_highestSubIndex_obj1280 },
                       { RW, uint32, sizeof (UNS32), (void*)&jsontest_obj1280_COB_ID_Client_to_Server_Transmit_SDO },
                       { RW, uint32, sizeof (UNS32), (void*)&jsontest_obj1280_COB_ID_Server_to_Client_Receive_SDO },
                       { RW|TO_BE_SAVE, uint8, sizeof (UNS8), (void*)&jsontest_obj1280_Node_ID_of_the_SDO_Server }
                     };

/* index 0x1281 :   Client SDO 2 Parameter. */
                    UNS8 jsontest_highestSubIndex_obj1281 = 3; /* number of subindex - 1*/
                    UNS32 jsontest_obj1281_COB_ID_Client_to_Server_Transmit_SDO = 0x0;	/* 0 */
                    UNS32 jsontest_obj1281_COB_ID_Server_to_Client_Receive_SDO = 0x0;	/* 0 */
                    UNS8 jsontest_obj1281_Node_ID_of_the_SDO_Server = 0x0;	/* 0 */
                    ODCallback_t jsontest_Index1281_callbacks[] = 
                     {
                       NULL,
                       NULL,
                       NULL,
                       NULL,
                     };
                    subindex jsontest_Index1281[] = 
                     {
                       { RO|TO_BE_SAVE, uint8, sizeof (UNS8), (void*)&jsontest_highestSubIndex_obj1281 },
                       { RW, uint32, sizeof (UNS32), (void*)&jsontest_obj1281_COB_ID_Client_to_Server_Transmit_SDO },
                       { RW, uint32, sizeof (UNS32), (void*)&jsontest_obj1281_COB_ID_Server_to_Client_Receive_SDO },
                       { RW|TO_BE_SAVE, uint8, sizeof (UNS8), (void*)&jsontest_obj1281_Node_ID_of_the_SDO_Server }
                     };

/* index 0x1282 :   Client SDO 3 Parameter. */
                    UNS8 jsontest_highestSubIndex_obj1282 = 3; /* number of subindex - 1*/
                    UNS32 jsontest_obj1282_COB_ID_Client_to_Server_Transmit_SDO = 0x0;	/* 0 */
                    UNS32 jsontest_obj1282_COB_ID_Server_to_Client_Receive_SDO = 0x0;	/* 0 */
                    UNS8 jsontest_obj1282_Node_ID_of_the_SDO_Server = 0x0;	/* 0 */
                    subindex jsontest_Index1282[] = 
                     {
                       { RO, uint8, sizeof (UNS8), (void*)&jsontest_highestSubIndex_obj1282 },
                       { RW, uint32, sizeof (UNS32), (void*)&jsontest_obj1282_COB_ID_Client_to_Server_Transmit_SDO },
                       { RW, uint32, sizeof (UNS32), (void*)&jsontest_obj1282_COB_ID_Server_to_Client_Receive_SDO },
                       { RW, uint8, sizeof (UNS8), (void*)&jsontest_obj1282_Node_ID_of_the_SDO_Server }
                     };

/* index 0x1400 :   Receive PDO 1 Parameter. */
                    UNS8 jsontest_highestSubIndex_obj1400 = 6; /* number of subindex - 1*/
                    UNS32 jsontest_obj1400_COB_ID_used_by_PDO = 0x200;	/* 512 */
                    UNS8 jsontest_obj1400_Transmission_Type = 0x0;	/* 0 */
                    UNS16 jsontest_obj1400_Inhibit_Time = 0x0;	/* 0 */
                    UNS8 jsontest_obj1400_Compatibility_Entry = 0x0;	/* 0 */
                    UNS16 jsontest_obj1400_Event_Timer = 0x0;	/* 0 */
                    UNS8 jsontest_obj1400_SYNC_start_value = 0x0;	/* 0 */
                    ODCallback_t jsontest_Index1400_callbacks[] = 
                     {
                       NULL,
                       NULL,
                       NULL,
                       NULL,
                       NULL,
                       NULL,
                       NULL,
                     };
                    subindex jsontest_Index1400[] = 
                     {
                       { RO|TO_BE_SAVE, uint8, sizeof (UNS8), (void*)&jsontest_highestSubIndex_obj1400 },
                       { RW, uint32, sizeof (UNS32), (void*)&jsontest_obj1400_COB_ID_used_by_PDO },
                       { RW, uint8, sizeof (UNS8), (void*)&jsontest_obj1400_Transmission_Type },
                       { RW, uint16, sizeof (UNS16), (void*)&jsontest_obj1400_Inhibit_Time },
                       { RW, uint8, sizeof (UNS8), (void*)&jsontest_obj1400_Compatibility_Entry },
                       { RW, uint16, sizeof (UNS16), (void*)&jsontest_obj1400_Event_Timer },
                       { RW|TO_BE_SAVE, uint8, sizeof (UNS8), (void*)&jsontest_obj1400_SYNC_start_value }
                     };

/* index 0x1401 :   Receive PDO 2 Parameter. */
                    UNS8 jsontest_highestSubIndex_obj1401 = 6; /* number of subindex - 1*/
                    UNS32 jsontest_obj1401_COB_ID_used_by_PDO = 0x300;	/* 768 */
                    UNS8 jsontest_obj1401_Transmission_Type = 0x0;	/* 0 */
                    UNS16 jsontest_obj1401_Inhibit_Time = 0x0;	/* 0 */
                    UNS8 jsontest_obj1401_Compatibility_Entry = 0x0;	/* 0 */
                    UNS16 jsontest_obj1401_Event_Timer = 0x0;	/* 0 */
                    UNS8 jsontest_obj1401_SYNC_start_value = 0x0;	/* 0 */
                    ODCallback_t jsontest_Index1401_callbacks[] = 
                     {
                       NULL,
                       NULL,
                       NULL,
                       NULL,
                       NULL,
                       NULL,
                       NULL,
                     };
                    subindex jsontest_Index1401[] = 
                     {
                       { RO|TO_BE_SAVE, uint8, sizeof (UNS8), (void*)&jsontest_highestSubIndex_obj1401 },
                       { RW, uint32, sizeof (UNS32), (void*)&jsontest_obj1401_COB_ID_used_by_PDO },
                       { RW, uint8, sizeof (UNS8), (void*)&jsontest_obj1401_Transmission_Type },
                       { RW, uint16, sizeof (UNS16), (void*)&jsontest_obj1401_Inhibit_Time },
                       { RW, uint8, sizeof (UNS8), (void*)&jsontest_obj1401_Compatibility_Entry },
                       { RW, uint16, sizeof (UNS16), (void*)&jsontest_obj1401_Event_Timer },
                       { RW|TO_BE_SAVE, uint8, sizeof (UNS8), (void*)&jsontest_obj1401_SYNC_start_value }
                     };

/* index 0x1402 :   Receive PDO 3 Parameter. */
                    UNS8 jsontest_highestSubIndex_obj1402 = 6; /* number of subindex - 1*/
                    UNS32 jsontest_obj1402_COB_ID_used_by_PDO = 0x400;	/* 1024 */
                    UNS8 jsontest_obj1402_Transmission_Type = 0x0;	/* 0 */
                    UNS16 jsontest_obj1402_Inhibit_Time = 0x0;	/* 0 */
                    UNS8 jsontest_obj1402_Compatibility_Entry = 0x0;	/* 0 */
                    UNS16 jsontest_obj1402_Event_Timer = 0x0;	/* 0 */
                    UNS8 jsontest_obj1402_SYNC_start_value = 0x0;	/* 0 */
                    subindex jsontest_Index1402[] = 
                     {
                       { RO, uint8, sizeof (UNS8), (void*)&jsontest_highestSubIndex_obj1402 },
                       { RW, uint32, sizeof (UNS32), (void*)&jsontest_obj1402_COB_ID_used_by_PDO },
                       { RW, uint8, sizeof (UNS8), (void*)&jsontest_obj1402_Transmission_Type },
                       { RW, uint16, sizeof (UNS16), (void*)&jsontest_obj1402_Inhibit_Time },
                       { RW, uint8, sizeof (UNS8), (void*)&jsontest_obj1402_Compatibility_Entry },
                       { RW, uint16, sizeof (UNS16), (void*)&jsontest_obj1402_Event_Timer },
                       { RW, uint8, sizeof (UNS8), (void*)&jsontest_obj1402_SYNC_start_value }
                     };

/* index 0x1600 :   Receive PDO 1 Mapping. */
                    UNS8 jsontest_highestSubIndex_obj1600 = 0; /* number of subindex - 1*/
                    UNS32 jsontest_obj1600[] = 
                    {
                    };
                    subindex jsontest_Index1600[] = 
                     {
                       { RW, uint8, sizeof (UNS8), (void*)&jsontest_highestSubIndex_obj1600 }
                     };

/* index 0x1601 :   Receive PDO 2 Mapping. */
                    UNS8 jsontest_highestSubIndex_obj1601 = 0; /* number of subindex - 1*/
                    UNS32 jsontest_obj1601[] = 
                    {
                    };
                    subindex jsontest_Index1601[] = 
                     {
                       { RW, uint8, sizeof (UNS8), (void*)&jsontest_highestSubIndex_obj1601 }
                     };

/* index 0x1602 :   Receive PDO 3 Mapping. */
                    UNS8 jsontest_highestSubIndex_obj1602 = 0; /* number of subindex - 1*/
                    UNS32 jsontest_obj1602[] = 
                    {
                    };
                    subindex jsontest_Index1602[] = 
                     {
                       { RW, uint8, sizeof (UNS8), (void*)&jsontest_highestSubIndex_obj1602 }
                     };

/* index 0x1F20 :   Store DCF. */
                    UNS8 jsontest_highestSubIndex_obj1F20 = 2; /* number of subindex - 1*/
                    UNS8* jsontest_obj1F20[] = 
                    {
                      "",
                      ""
                    };
                    ODCallback_t jsontest_Index1F20_callbacks[] = 
                     {
                       NULL,
                       NULL,
                       NULL,
                     };
                    subindex jsontest_Index1F20[] = 
                     {
                       { RO|TO_BE_SAVE, uint8, sizeof (UNS8), (void*)&jsontest_highestSubIndex_obj1F20 },
                       { RW|TO_BE_SAVE, domain, 0, (void*)&jsontest_obj1F20[0] },
                       { RW|TO_BE_SAVE, domain, 0, (void*)&jsontest_obj1F20[1] }
                     };

/* index 0x2000 :   Mapped variable VAR */
                    ODCallback_t VAR_callbacks[] = 
                     {
                       NULL,
                     };
                    subindex jsontest_Index2000[] = 
                     {
                       { RW|TO_BE_SAVE, uint8, sizeof (UNS8), (void*)&VAR }
                     };

/* index 0x2001 :   Mapped variable ARRAY */
                    UNS8 jsontest_highestSubIndex_obj2001 = 2; /* number of subindex - 1*/
                    ODCallback_t ARRAY_callbacks[] = 
                     {
                       NULL,
                       NULL,
                       NULL,
                     };
                    subindex jsontest_Index2001[] = 
                     {
                       { RO|TO_BE_SAVE, uint8, sizeof (UNS8), (void*)&jsontest_highestSubIndex_obj2001 },
                       { RO, int8, sizeof (INTEGER8), (void*)&ARRAY[0] },
                       { RO, int8, sizeof (INTEGER8), (void*)&ARRAY[1] }
                     };

/* index 0x2002 :   Mapped variable RECORD */
                    UNS8 jsontest_highestSubIndex_obj2002 = 2; /* number of subindex - 1*/
                    ODCallback_t RECORD_callbacks[] = 
                     {
                       NULL,
                       NULL,
                       NULL,
                     };
                    subindex jsontest_Index2002[] = 
                     {
                       { RO|TO_BE_SAVE, uint8, sizeof (UNS8), (void*)&jsontest_highestSubIndex_obj2002 },
                       { RW, uint8, sizeof (UNS8), (void*)&RECORD_RECORD_1 },
                       { RW|TO_BE_SAVE, int16, sizeof (INTEGER16), (void*)&RECORD_RECORD_2 }
                     };

/* index 0x6000 :   Mapped variable VAR: Global Interrupt Enable Digital */
                    ODCallback_t VAR_Global_Interrupt_Enable_Digital_callbacks[] = 
                     {
                       NULL,
                     };
                    subindex jsontest_Index6000[] = 
                     {
                       { RW|TO_BE_SAVE, boolean, sizeof (UNS8), (void*)&Global_Interrupt_Enable_Digital_Sure }
                     };

/* index 0x6100 :   Mapped variable RECORD: Software position limit */
                    UNS8 jsontest_highestSubIndex_obj6100 = 2; /* number of subindex - 1*/
                    ODCallback_t RECORD_Software_position_limit_callbacks[] = 
                     {
                       NULL,
                       NULL,
                       NULL,
                     };
                    subindex jsontest_Index6100[] = 
                     {
                       { RO|TO_BE_SAVE, uint8, sizeof (UNS8), (void*)&jsontest_highestSubIndex_obj6100 },
                       { RW, int32, sizeof (INTEGER32), (void*)&RECORD_Software_position_limit_Minimal_position_limit },
                       { RW|TO_BE_SAVE, int32, sizeof (INTEGER32), (void*)&RECORD_Software_position_limit_Maximal_position_limit }
                     };

/* index 0x6180 :   Mapped variable RECORD: AL Action */
                    UNS8 jsontest_highestSubIndex_obj6180 = 6; /* number of subindex - 1*/
                    ODCallback_t RECORD_AL_Action_callbacks[] = 
                     {
                       NULL,
                       NULL,
                       NULL,
                       NULL,
                       NULL,
                       NULL,
                       NULL,
                     };
                    subindex jsontest_Index6180[] = 
                     {
                       { RO|TO_BE_SAVE, uint8, sizeof (UNS8), (void*)&jsontest_highestSubIndex_obj6180 },
                       { RW, int16, sizeof (INTEGER16), (void*)&RECORD_AL_Action_AL_1_Action_1 },
                       { RW, int16, sizeof (INTEGER16), (void*)&RECORD_AL_Action_AL_1_Action_2 },
                       { RW, int16, sizeof (INTEGER16), (void*)&RECORD_AL_Action_AL_1_Action_3 },
                       { RW, int16, sizeof (INTEGER16), (void*)&RECORD_AL_Action_AL_1_Action_4 },
                       { RW, int16, sizeof (INTEGER16), (void*)&RECORD_AL_Action_AL_1_Action_5 },
                       { RW|TO_BE_SAVE, int16, sizeof (INTEGER16), (void*)&RECORD_AL_Action_AL_1_Action_6 }
                     };

/* index 0x6200 :   Mapped variable ARRAY: Acceleration Value */
                    UNS8 jsontest_highestSubIndex_obj6200 = 2; /* number of subindex - 1*/
                    ODCallback_t ARRAY_Acceleration_Value_callbacks[] = 
                     {
                       NULL,
                       NULL,
                       NULL,
                     };
                    subindex jsontest_Index6200[] = 
                     {
                       { RO|TO_BE_SAVE, uint8, sizeof (UNS8), (void*)&jsontest_highestSubIndex_obj6200 },
                       { RO, int16, sizeof (INTEGER16), (void*)&ARRAY_Acceleration_Value[0] },
                       { RO|TO_BE_SAVE, int16, sizeof (INTEGER16), (void*)&ARRAY_Acceleration_Value[1] }
                     };

/* index 0x6300 :   Mapped variable NVAR: Test profile 1 */
                    ODCallback_t NVAR_Test_profile_1_callbacks[] = 
                     {
                       NULL,
                     };
                    subindex jsontest_Index6300[] = 
                     {
                       { RO|TO_BE_SAVE, uint32, sizeof (UNS32), (void*)&Device_Type_1_and_0 }
                     };

/* index 0x6302 :   Mapped variable NVAR: Test profile 2 */
                    subindex jsontest_Index6302[] = 
                     {
                       { RO, uint32, sizeof (UNS32), (void*)&Device_Type_2_and_0 }
                     };

/* index 0x6400 :   Mapped variable NARRAY: CAM1 Low Limit */
                    UNS8 jsontest_highestSubIndex_obj6400 = 2; /* number of subindex - 1*/
                    ODCallback_t NARRAY_CAM1_Low_Limit_callbacks[] = 
                     {
                       NULL,
                       NULL,
                       NULL,
                     };
                    subindex jsontest_Index6400[] = 
                     {
                       { RO|TO_BE_SAVE, uint8, sizeof (UNS8), (void*)&jsontest_highestSubIndex_obj6400 },
                       { RW, int32, sizeof (INTEGER32), (void*)&NARRAY_CAM1_Low_Limit[0] },
                       { RW|TO_BE_SAVE, int32, sizeof (INTEGER32), (void*)&NARRAY_CAM1_Low_Limit[1] }
                     };

/* index 0x6402 :   Mapped variable NARRAY: CAM2 Low Limit */
                    UNS8 jsontest_highestSubIndex_obj6402 = 0; /* number of subindex - 1*/
                    subindex jsontest_Index6402[] = 
                     {
                       { RO, uint8, sizeof (UNS8), (void*)&jsontest_highestSubIndex_obj6402 }
                     };

/* index 0x6500 :   Mapped variable NRECORD: Receive PDO 1 Parameter */
                    UNS8 jsontest_highestSubIndex_obj6500 = 6; /* number of subindex - 1*/
                    ODCallback_t NRECORD_Receive_PDO_1_Parameter_callbacks[] = 
                     {
                       NULL,
                       NULL,
                       NULL,
                       NULL,
                       NULL,
                       NULL,
                       NULL,
                     };
                    subindex jsontest_Index6500[] = 
                     {
                       { RO|TO_BE_SAVE, uint8, sizeof (UNS8), (void*)&jsontest_highestSubIndex_obj6500 },
                       { RW, uint32, sizeof (UNS32), (void*)&NRECORD_Receive_PDO_1_Parameter_COB_ID_used_by_PDO },
                       { RW, uint8, sizeof (UNS8), (void*)&NRECORD_Receive_PDO_1_Parameter_Transmission_Type },
                       { RW, uint16, sizeof (UNS16), (void*)&NRECORD_Receive_PDO_1_Parameter_Inhibit_Time },
                       { RW, uint8, sizeof (UNS8), (void*)&NRECORD_Receive_PDO_1_Parameter_Compatibility_Entry },
                       { RW, uint16, sizeof (UNS16), (void*)&NRECORD_Receive_PDO_1_Parameter_Event_Timer },
                       { RW|TO_BE_SAVE, uint8, sizeof (UNS8), (void*)&NRECORD_Receive_PDO_1_Parameter_SYNC_start_value }
                     };

/* index 0x6502 :   Mapped variable NRECORD: Receive PDO 2 Parameter */
                    UNS8 jsontest_highestSubIndex_obj6502 = 0; /* number of subindex - 1*/
                    subindex jsontest_Index6502[] = 
                     {
                       { RO, uint8, sizeof (UNS8), (void*)&jsontest_highestSubIndex_obj6502 }
                     };

/* index 0x6580 :   Mapped variable NRECORD: AL 1 Action */
                    UNS8 jsontest_highestSubIndex_obj6580 = 6; /* number of subindex - 1*/
                    ODCallback_t NRECORD_AL_1_Action_callbacks[] = 
                     {
                       NULL,
                       NULL,
                       NULL,
                       NULL,
                       NULL,
                       NULL,
                       NULL,
                     };
                    subindex jsontest_Index6580[] = 
                     {
                       { RO|TO_BE_SAVE, uint8, sizeof (UNS8), (void*)&jsontest_highestSubIndex_obj6580 },
                       { RW, uint32, sizeof (UNS32), (void*)&NRECORD_AL_1_Action_AL_1_Action_1 },
                       { RW, uint32, sizeof (UNS32), (void*)&NRECORD_AL_1_Action_AL_1_Action_2 },
                       { RW, uint32, sizeof (UNS32), (void*)&NRECORD_AL_1_Action_AL_1_Action_3 },
                       { RW|TO_BE_SAVE, uint32, sizeof (UNS32), (void*)&NRECORD_AL_1_Action_AL_1_Action_4 },
                       { RW, uint32, sizeof (UNS32), (void*)&NRECORD_AL_1_Action_AL_1_Action_5 },
                       { RW|TO_BE_SAVE, uint32, sizeof (UNS32), (void*)&NRECORD_AL_1_Action_AL_1_Action_6 }
                     };

/* index 0x6600 :   Mapped variable Producer Heartbeat Time */
                    ODCallback_t Producer_Heartbeat_Time_callbacks[] = 
                     {
                       NULL,
                     };
                    subindex jsontest_Index6600[] = 
                     {
                       { RW|TO_BE_SAVE, uint16, sizeof (UNS16), (void*)&Producer_Heartbeat_Time }
                     };

/**************************************************************************/
/* Declaration of pointed variables                                       */
/**************************************************************************/

const indextable jsontest_objdict[] =
{
  { (subindex*)jsontest_Index1000,sizeof(jsontest_Index1000)/sizeof(jsontest_Index1000[0]), 0x1000},
  { (subindex*)jsontest_Index1001,sizeof(jsontest_Index1001)/sizeof(jsontest_Index1001[0]), 0x1001},
  { (subindex*)jsontest_Index1018,sizeof(jsontest_Index1018)/sizeof(jsontest_Index1018[0]), 0x1018},
  { (subindex*)jsontest_Index1280,sizeof(jsontest_Index1280)/sizeof(jsontest_Index1280[0]), 0x1280},
  { (subindex*)jsontest_Index1281,sizeof(jsontest_Index1281)/sizeof(jsontest_Index1281[0]), 0x1281},
  { (subindex*)jsontest_Index1282,sizeof(jsontest_Index1282)/sizeof(jsontest_Index1282[0]), 0x1282},
  { (subindex*)jsontest_Index1400,sizeof(jsontest_Index1400)/sizeof(jsontest_Index1400[0]), 0x1400},
  { (subindex*)jsontest_Index1401,sizeof(jsontest_Index1401)/sizeof(jsontest_Index1401[0]), 0x1401},
  { (subindex*)jsontest_Index1402,sizeof(jsontest_Index1402)/sizeof(jsontest_Index1402[0]), 0x1402},
  { (subindex*)jsontest_Index1600,sizeof(jsontest_Index1600)/sizeof(jsontest_Index1600[0]), 0x1600},
  { (subindex*)jsontest_Index1601,sizeof(jsontest_Index1601)/sizeof(jsontest_Index1601[0]), 0x1601},
  { (subindex*)jsontest_Index1602,sizeof(jsontest_Index1602)/sizeof(jsontest_Index1602[0]), 0x1602},
  { (subindex*)jsontest_Index1F20,sizeof(jsontest_Index1F20)/sizeof(jsontest_Index1F20[0]), 0x1F20},
  { (subindex*)jsontest_Index2000,sizeof(jsontest_Index2000)/sizeof(jsontest_Index2000[0]), 0x2000},
  { (subindex*)jsontest_Index2001,sizeof(jsontest_Index2001)/sizeof(jsontest_Index2001[0]), 0x2001},
  { (subindex*)jsontest_Index2002,sizeof(jsontest_Index2002)/sizeof(jsontest_Index2002[0]), 0x2002},
  { (subindex*)jsontest_Index6000,sizeof(jsontest_Index6000)/sizeof(jsontest_Index6000[0]), 0x6000},
  { (subindex*)jsontest_Index6100,sizeof(jsontest_Index6100)/sizeof(jsontest_Index6100[0]), 0x6100},
  { (subindex*)jsontest_Index6180,sizeof(jsontest_Index6180)/sizeof(jsontest_Index6180[0]), 0x6180},
  { (subindex*)jsontest_Index6200,sizeof(jsontest_Index6200)/sizeof(jsontest_Index6200[0]), 0x6200},
  { (subindex*)jsontest_Index6300,sizeof(jsontest_Index6300)/sizeof(jsontest_Index6300[0]), 0x6300},
  { (subindex*)jsontest_Index6302,sizeof(jsontest_Index6302)/sizeof(jsontest_Index6302[0]), 0x6302},
  { (subindex*)jsontest_Index6400,sizeof(jsontest_Index6400)/sizeof(jsontest_Index6400[0]), 0x6400},
  { (subindex*)jsontest_Index6402,sizeof(jsontest_Index6402)/sizeof(jsontest_Index6402[0]), 0x6402},
  { (subindex*)jsontest_Index6500,sizeof(jsontest_Index6500)/sizeof(jsontest_Index6500[0]), 0x6500},
  { (subindex*)jsontest_Index6502,sizeof(jsontest_Index6502)/sizeof(jsontest_Index6502[0]), 0x6502},
  { (subindex*)jsontest_Index6580,sizeof(jsontest_Index6580)/sizeof(jsontest_Index6580[0]), 0x6580},
  { (subindex*)jsontest_Index6600,sizeof(jsontest_Index6600)/sizeof(jsontest_Index6600[0]), 0x6600},
};

const indextable * jsontest_scanIndexOD (UNS16 wIndex, UNS32 * errorCode, ODCallback_t **callbacks)
{
    int i;
    *callbacks = NULL;
    switch(wIndex){
       case 0x1000: i = 0;*callbacks = jsontest_Index1000_callbacks; break;
       case 0x1001: i = 1;break;
       case 0x1018: i = 2;*callbacks = jsontest_Index1018_callbacks; break;
       case 0x1280: i = 3;*callbacks = jsontest_Index1280_callbacks; break;
       case 0x1281: i = 4;*callbacks = jsontest_Index1281_callbacks; break;
       case 0x1282: i = 5;break;
       case 0x1400: i = 6;*callbacks = jsontest_Index1400_callbacks; break;
       case 0x1401: i = 7;*callbacks = jsontest_Index1401_callbacks; break;
       case 0x1402: i = 8;break;
       case 0x1600: i = 9;break;
       case 0x1601: i = 10;break;
       case 0x1602: i = 11;break;
       case 0x1F20: i = 12;*callbacks = jsontest_Index1F20_callbacks; break;
       case 0x2000: i = 13;*callbacks = VAR_callbacks; break;
       case 0x2001: i = 14;*callbacks = ARRAY_callbacks; break;
       case 0x2002: i = 15;*callbacks = RECORD_callbacks; break;
       case 0x6000: i = 16;*callbacks = VAR_Global_Interrupt_Enable_Digital_callbacks; break;
       case 0x6100: i = 17;*callbacks = RECORD_Software_position_limit_callbacks; break;
       case 0x6180: i = 18;*callbacks = RECORD_AL_Action_callbacks; break;
       case 0x6200: i = 19;*callbacks = ARRAY_Acceleration_Value_callbacks; break;
       case 0x6300: i = 20;*callbacks = NVAR_Test_profile_1_callbacks; break;
       case 0x6302: i = 21;break;
       case 0x6400: i = 22;*callbacks = NARRAY_CAM1_Low_Limit_callbacks; break;
       case 0x6402: i = 23;break;
       case 0x6500: i = 24;*callbacks = NRECORD_Receive_PDO_1_Parameter_callbacks; break;
       case 0x6502: i = 25;break;
       case 0x6580: i = 26;*callbacks = NRECORD_AL_1_Action_callbacks; break;
       case 0x6600: i = 27;*callbacks = Producer_Heartbeat_Time_callbacks; break;
       default:
            *errorCode = OD_NO_SUCH_OBJECT;
            return NULL;
    }
    *errorCode = OD_SUCCESSFUL;
    return &jsontest_objdict[i];
}

/*
 * To count at which received SYNC a PDO must be sent.
 * Even if no pdoTransmit are defined, at least one entry is computed
 * for compilations issues.
 */
s_PDO_status jsontest_PDO_status[1] = {s_PDO_status_Initializer};

const quick_index jsontest_firstIndex = {
  0, /* SDO_SVR */
  3, /* SDO_CLT */
  6, /* PDO_RCV */
  9, /* PDO_RCV_MAP */
  0, /* PDO_TRS */
  0 /* PDO_TRS_MAP */
};

const quick_index jsontest_lastIndex = {
  0, /* SDO_SVR */
  5, /* SDO_CLT */
  8, /* PDO_RCV */
  11, /* PDO_RCV_MAP */
  0, /* PDO_TRS */
  0 /* PDO_TRS_MAP */
};

const UNS16 jsontest_ObjdictSize = sizeof(jsontest_objdict)/sizeof(jsontest_objdict[0]);

CO_Data jsontest_Data = CANOPEN_NODE_DATA_INITIALIZER(jsontest);

