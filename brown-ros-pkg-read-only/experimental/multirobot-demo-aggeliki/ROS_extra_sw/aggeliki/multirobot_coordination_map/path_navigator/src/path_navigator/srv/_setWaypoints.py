# autogenerated by genmsg_py from setWaypointsRequest.msg. Do not edit.
import roslib.message
import struct

import path_navigator.msg
import roslib.msg
import map_loader.msg
import position_tracker.msg

class setWaypointsRequest(roslib.message.Message):
  _md5sum = "fd20651d4e00349491fe00ca51b68d1d"
  _type = "path_navigator/setWaypointsRequest"
  _has_header = False #flag to mark the presence of a Header object
  _full_text = """path_navigator/Waypoints w

================================================================================
MSG: path_navigator/Waypoints
map_loader/Node[] waypoints

================================================================================
MSG: map_loader/Node
int32 id
#Node previous
int32 distanceFromStart
position_tracker/Position p


================================================================================
MSG: position_tracker/Position
Header header
float64 x
float64 y
float64 theta

================================================================================
MSG: roslib/Header
# Standard metadata for higher-level stamped data types.
# This is generally used to communicate timestamped data 
# in a particular coordinate frame.
# 
# sequence ID: consecutively increasing ID 
uint32 seq
#Two-integer timestamp that is expressed as:
# * stamp.secs: seconds (stamp_secs) since epoch
# * stamp.nsecs: nanoseconds since stamp_secs
# time-handling sugar is provided by the client library
time stamp
#Frame this data is associated with
# 0: no frame
# 1: global frame
string frame_id

"""
  __slots__ = ['w']
  _slot_types = ['path_navigator/Waypoints']

  ## Constructor. Any message fields that are implicitly/explicitly
  ## set to None will be assigned a default value. The recommend
  ## use is keyword arguments as this is more robust to future message
  ## changes.  You cannot mix in-order arguments and keyword arguments.
  ##
  ## The available fields are:
  ##   w
  ##
  ## @param self: self
  ## @param args: complete set of field values, in .msg order
  ## @param kwds: use keyword arguments corresponding to message field names
  ## to set specific fields. 
  def __init__(self, *args, **kwds):
    if args or kwds:
      super(setWaypointsRequest, self).__init__(*args, **kwds)
      #message fields cannot be None, assign default values for those that are
      if self.w is None:
        self.w = path_navigator.msg.Waypoints()
    else:
      self.w = path_navigator.msg.Waypoints()

  ## internal API method
  def _get_types(self): return self._slot_types

  ## serialize message into buffer
  ## @param buff StringIO: buffer
  def serialize(self, buff):
    try:
      #serialize self.w.waypoints
      length = len(self.w.waypoints)
      buff.write(struct.pack('<I', length))
      for val1 in self.w.waypoints:
        buff.write(struct.pack('<2i', val1.id, val1.distanceFromStart))
        buff.write(struct.pack('<I', val1.p.header.seq))
        buff.write(struct.pack('<2I', val1.p.header.stamp.secs, val1.p.header.stamp.nsecs))
        length = len(val1.p.header.frame_id)
        #serialize val1.p.header.frame_id
        buff.write(struct.pack('<I%ss'%length, length, val1.p.header.frame_id))
        buff.write(struct.pack('<3d', val1.p.x, val1.p.y, val1.p.theta))
    except struct.error, se: self._check_types(se)
    except TypeError, te: self._check_types(te)

  ## unpack serialized message in str into this message instance
  ## @param self: self
  ## @param str str: byte array of serialized message
  def deserialize(self, str):
    try:
      if self.w is None:
        self.w = path_navigator.msg.Waypoints()
      end = 0
      #deserialize self.w.waypoints
      start = end
      end += 4
      (length,) = struct.unpack('<I',str[start:end])
      self.w.waypoints = []
      for i in xrange(0, length):
        val1 = map_loader.msg.Node()
        start = end
        end += 8
        (val1.id, val1.distanceFromStart,) = struct.unpack('<2i',str[start:end])
        start = end
        end += 4
        (val1.p.header.seq,) = struct.unpack('<I',str[start:end])
        start = end
        end += 8
        (val1.p.header.stamp.secs, val1.p.header.stamp.nsecs,) = struct.unpack('<2I',str[start:end])
        start = end
        end += 4
        (length,) = struct.unpack('<I',str[start:end])
        #deserialize val1.p.header.frame_id
        pattern = '<%ss'%length
        start = end
        end += struct.calcsize(pattern)
        (val1.p.header.frame_id,) = struct.unpack(pattern, str[start:end])
        start = end
        end += 24
        (val1.p.x, val1.p.y, val1.p.theta,) = struct.unpack('<3d',str[start:end])
        self.w.waypoints.append(val1)
      return self
    except struct.error, e:
      raise roslib.message.DeserializationError(e) #most likely buffer underfill


  ## serialize message with numpy array types into buffer
  ## @param self: self
  ## @param buff StringIO: buffer
  ## @param numpy module: numpy python module
  def serialize_numpy(self, buff, numpy):
    try:
      #serialize self.w.waypoints
      length = len(self.w.waypoints)
      buff.write(struct.pack('<I', length))
      for val1 in self.w.waypoints:
        buff.write(struct.pack('<2i', val1.id, val1.distanceFromStart))
        buff.write(struct.pack('<I', val1.p.header.seq))
        buff.write(struct.pack('<2I', val1.p.header.stamp.secs, val1.p.header.stamp.nsecs))
        length = len(val1.p.header.frame_id)
        #serialize val1.p.header.frame_id
        buff.write(struct.pack('<I%ss'%length, length, val1.p.header.frame_id))
        buff.write(struct.pack('<3d', val1.p.x, val1.p.y, val1.p.theta))
    except struct.error, se: self._check_types(se)
    except TypeError, te: self._check_types(te)

  ## unpack serialized message in str into this message instance using numpy for array types
  ## @param self: self
  ## @param str str: byte array of serialized message
  ## @param numpy module: numpy python module
  def deserialize_numpy(self, str, numpy):
    try:
      if self.w is None:
        self.w = path_navigator.msg.Waypoints()
      end = 0
      #deserialize self.w.waypoints
      start = end
      end += 4
      (length,) = struct.unpack('<I',str[start:end])
      self.w.waypoints = []
      for i in xrange(0, length):
        val1 = map_loader.msg.Node()
        start = end
        end += 8
        (val1.id, val1.distanceFromStart,) = struct.unpack('<2i',str[start:end])
        start = end
        end += 4
        (val1.p.header.seq,) = struct.unpack('<I',str[start:end])
        start = end
        end += 8
        (val1.p.header.stamp.secs, val1.p.header.stamp.nsecs,) = struct.unpack('<2I',str[start:end])
        start = end
        end += 4
        (length,) = struct.unpack('<I',str[start:end])
        #deserialize val1.p.header.frame_id
        pattern = '<%ss'%length
        start = end
        end += struct.calcsize(pattern)
        (val1.p.header.frame_id,) = struct.unpack(pattern, str[start:end])
        start = end
        end += 24
        (val1.p.x, val1.p.y, val1.p.theta,) = struct.unpack('<3d',str[start:end])
        self.w.waypoints.append(val1)
      return self
    except struct.error, e:
      raise roslib.message.DeserializationError(e) #most likely buffer underfill

# autogenerated by genmsg_py from setWaypointsResponse.msg. Do not edit.
import roslib.message
import struct


class setWaypointsResponse(roslib.message.Message):
  _md5sum = "32970d3e7822c2c952eeb697b73b10b5"
  _type = "path_navigator/setWaypointsResponse"
  _has_header = False #flag to mark the presence of a Header object
  _full_text = """bool out



"""
  __slots__ = ['out']
  _slot_types = ['bool']

  ## Constructor. Any message fields that are implicitly/explicitly
  ## set to None will be assigned a default value. The recommend
  ## use is keyword arguments as this is more robust to future message
  ## changes.  You cannot mix in-order arguments and keyword arguments.
  ##
  ## The available fields are:
  ##   out
  ##
  ## @param self: self
  ## @param args: complete set of field values, in .msg order
  ## @param kwds: use keyword arguments corresponding to message field names
  ## to set specific fields. 
  def __init__(self, *args, **kwds):
    if args or kwds:
      super(setWaypointsResponse, self).__init__(*args, **kwds)
      #message fields cannot be None, assign default values for those that are
      if self.out is None:
        self.out = False
    else:
      self.out = False

  ## internal API method
  def _get_types(self): return self._slot_types

  ## serialize message into buffer
  ## @param buff StringIO: buffer
  def serialize(self, buff):
    try:
      buff.write(struct.pack('<B', self.out))
    except struct.error, se: self._check_types(se)
    except TypeError, te: self._check_types(te)

  ## unpack serialized message in str into this message instance
  ## @param self: self
  ## @param str str: byte array of serialized message
  def deserialize(self, str):
    try:
      end = 0
      start = end
      end += 1
      (self.out,) = struct.unpack('<B',str[start:end])
      self.out = bool(self.out)
      return self
    except struct.error, e:
      raise roslib.message.DeserializationError(e) #most likely buffer underfill


  ## serialize message with numpy array types into buffer
  ## @param self: self
  ## @param buff StringIO: buffer
  ## @param numpy module: numpy python module
  def serialize_numpy(self, buff, numpy):
    try:
      buff.write(struct.pack('<B', self.out))
    except struct.error, se: self._check_types(se)
    except TypeError, te: self._check_types(te)

  ## unpack serialized message in str into this message instance using numpy for array types
  ## @param self: self
  ## @param str str: byte array of serialized message
  ## @param numpy module: numpy python module
  def deserialize_numpy(self, str, numpy):
    try:
      end = 0
      start = end
      end += 1
      (self.out,) = struct.unpack('<B',str[start:end])
      self.out = bool(self.out)
      return self
    except struct.error, e:
      raise roslib.message.DeserializationError(e) #most likely buffer underfill

class setWaypoints(roslib.message.ServiceDefinition):
  _type          = 'path_navigator/setWaypoints'
  _md5sum = '1f8729137cbc7f8cd3ca51a66869d663'
  _request_class  = setWaypointsRequest
  _response_class = setWaypointsResponse