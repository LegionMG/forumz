drop table if exists entries;
create table entries (
  id integer primary key autoincrement,
  title text not null,
  user text not null,
  text text not null
);

drop table if exists users;
create table users (
  id integer primary key autoincrement,
  nickname text not null unique,
  role int not null, 
  password text not null
);

drop table if exists messages;
create table messages (
  mid integer primary key autoincrement,
  uid integer not null,
  tid integer not null,
  time date not null,
  msg text not null
);

drop table if exists topics;
create table topics (
  tid integer primary key autoincrement,
  sid integer not null,
  tname text not null,
  tdesc text not null
);

drop table if exists sections;
create table sections (
  sid integer primary key autoincrement,
  sname text not null,
  sdesc text not null
);