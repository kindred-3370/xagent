CREATE TABLE `t_flight_dynamic_report` (
  `sn` varchar(64) NULL COMMENT "唯一产品识别码",
  `id` varchar(256) NOT NULL COMMENT "主键",
  `fp_id` varchar(32) NULL COMMENT "飞行计划申请(任务)ID",
  `order_id` varchar(256) NULL COMMENT "飞行记录编号",
  `flight_status` varchar(16) NULL COMMENT "飞行状态",
  `manufacturer_id` varchar(32) NULL COMMENT "统一社会信用代码",
  `uas_id` varchar(16) NULL DEFAULT "UAS-DEFAULT" COMMENT "无人驾驶航空器实名登记号",
  `uav_type` varchar(32) NULL COMMENT "无人机类型",
  `time_stamp` varchar(32) NULL COMMENT "当前时间",
  `uav_model` varchar(32) NULL COMMENT "产品型号",
  `coordinate` int NULL COMMENT "坐标系类型",
  `longitude` bigint NULL COMMENT "经度",
  `latitude` bigint NULL COMMENT "纬度",
  `height_altitype` int NULL COMMENT "真高类型",
  `height` int NULL COMMENT "真高",
  `altitude` int NULL COMMENT "海拔高度",
  `vs` int NULL COMMENT "垂直飞行速度值",
  `gs` int NULL COMMENT "水平飞行速度值",
  `course` int NULL DEFAULT "999" COMMENT "航迹角",
  `uav_auth_info` text NULL COMMENT "无人机实名信息",
  `source` varchar(32) NULL COMMENT "数据来源",
  `audit_sts` varchar(4) NULL COMMENT "飞行计划申请状态：1:批准、不予批准、3:审批中、4:不予受理、5其他",
  `del_flag` int NULL DEFAULT "0" COMMENT "删除状态(0-正常,1-已删除)",
  `create_by` varchar(50) NULL COMMENT "创建人",
  `create_time` datetime NULL COMMENT "创建日期",
  `update_by` varchar(50) NULL COMMENT "更新人",
  `update_time` datetime NULL COMMENT "更新日期",
  `sys_org_code` varchar(64) NULL COMMENT "所属部门"
) ENGINE=OLAP
DUPLICATE KEY(`sn`)
COMMENT '无人机飞行动态'
DISTRIBUTED BY HASH(`sn`) BUCKETS 16
PROPERTIES (
"replication_allocation" = "tag.location.default: 3",
"min_load_replica_num" = "-1",
"is_being_synced" = "false",
"storage_medium" = "hdd",
"storage_format" = "V2",
"inverted_index_storage_format" = "V1",
"light_schema_change" = "true",
"disable_auto_compaction" = "false",
"enable_single_replica_compaction" = "false",
"group_commit_interval_ms" = "10000",
"group_commit_data_bytes" = "134217728"
);
