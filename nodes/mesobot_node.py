#!/usr/bin/env python3

import rospy

from sonardyne_msgs.msg import SMS
from geographic_msgs.msg import GeoPointStamped
from geographic_msgs.msg import GeoPoseStamped
from project11_msgs.msg import Heartbeat
from project11_msgs.msg import KeyValue as HBKeyValue
from std_msgs.msg import Float32

import math

import project11
from tf.transformations import quaternion_about_axis

last_state = None

last_positon_time = None

def smsCallback( msg):
  global last_state
  #print (msg)

  decoder = {'H:':'Heading',
             'D:':'Depth',
             'B:':'Battery',
             'R:':'Radiometer',
             'S:':'Flows',
             'C:':'Command',
             'M:':'Status',
             'J:':'Drive'
             }

  if msg.message.startswith('H: '):
    parts = msg.message.split()
    print (parts)
    key = None
    values = []

    state = {'timestamp':rospy.Time.now()}
    hb = Heartbeat()
    hb.header.stamp = state['timestamp']
    for p in parts:
      if p in decoder.keys():
        if key is not None:
          kv = HBKeyValue()
          kv.key = decoder[key]
          kv.value = ', '.join(values)
          hb.values.append(kv)
        key = p
        values = []
      else:
        values.append(p)
        if key == 'H:' and not 'heading' in state:
          try:
            state['heading'] = float(p)
            hmsg = Float32()
            hmsg.data = state['heading']
            heading_pub.publish(hmsg)
          except ValueError:
            pass
        if key == 'D:' and not 'depth' in state:
          try:
            state['depth'] = float(p)
            dmsg = Float32()
            dmsg.data = state['depth']
            depth_pub.publish(dmsg)
          except ValueError:
            pass
        if key == 'B:' and not 'battery' in state:
          try:
            state['battery'] = float(p)
            bmsg = Float32()
            bmsg.data = state['battery']
            battery_pub.publish(bmsg)
          except ValueError:
            pass
        if key == 'R:' and not 'radiometer' in state:
          try:
            state['radiometer'] = float(p)
            rmsg = Float32()
            rmsg.data = state['radiometer']
            radiometer_pub.publish(rmsg)
          except ValueError:
            pass

    if key is not None:
      kv = HBKeyValue()
      kv.key = decoder[key]
      kv.value = ', '.join(values)
      hb.values.append(kv)
    heartbeat_pub.publish(hb)
    last_state = state
    



def positionCallback(msg):
  gps = GeoPoseStamped()
  gps.header = msg.header
  gps.pose.position = msg.position
  if last_state is not None:
    if 'timestamp' in last_state and rospy.Time().now() - last_state['timestamp'] < rospy.Duration(secs=300):
      if 'depth' in last_state:
        gps.pose.position.altitude = -last_state['depth']
      if 'heading' in last_state:
        yaw = math.radians(project11.nav.headingToYaw(last_state['heading']))
        quat = quaternion_about_axis(yaw, (0,0,1))
        gps.pose.orientation.x = quat[0]
        gps.pose.orientation.y = quat[1]
        gps.pose.orientation.z = quat[2]
        gps.pose.orientation.w = quat[3]
  position_pub.publish(gps)
  last_positon_time = gps.header.stamp
  #print (msg)

def backupPositionCallback(msg):
  gps = GeoPoseStamped()
  gps.header = msg.header
  gps.pose.position = msg.position
  if last_state is not None:
    if 'timestamp' in last_state and rospy.Time().now() - last_state['timestamp'] < rospy.Duration(secs=300):
      if 'depth' in last_state:
        gps.pose.position.altitude = -last_state['depth']
      if 'heading' in last_state:
        yaw = math.radians(project11.nav.headingToYaw(last_state['heading']))
        quat = quaternion_about_axis(yaw, (0,0,1))
        gps.pose.orientation.x = quat[0]
        gps.pose.orientation.y = quat[1]
        gps.pose.orientation.z = quat[2]
        gps.pose.orientation.w = quat[3]
  if last_positon_time is None or msg.header.stamp - last_positon_time > rospy.Duration(30):
    position_pub.publish(gps)
  #print (msg)


rospy.init_node('mesobot', anonymous=False)

sms_sub = rospy.Subscriber('sms', SMS, smsCallback)
position_sub = rospy.Subscriber('position', GeoPointStamped, positionCallback)
backup_position_sub = rospy.Subscriber('backup_position', GeoPointStamped, backupPositionCallback)

heartbeat_pub = rospy.Publisher('project11/heartbeat', Heartbeat, queue_size=1)
position_pub = rospy.Publisher('nav/position', GeoPoseStamped, queue_size=1)

heading_pub = rospy.Publisher('heading', Float32, queue_size=1)
depth_pub = rospy.Publisher('depth', Float32, queue_size=1)
battery_pub = rospy.Publisher('battery', Float32, queue_size=1)
radiometer_pub = rospy.Publisher('radiometer', Float32, queue_size=1)

rospy.spin()
