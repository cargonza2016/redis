# Overview

Redis (<http://redis.io>) is an open source, advanced key-value cache and
store. It is often referred to as a data structure server since keys can
contain strings, hashes, lists, sets, sorted sets, bitmaps and hyperloglogs.
In order to achieve its outstanding performance, Redis works with an in-memory
dataset that can be written to disk. Redis also supports master-slave
asynchronous replication.

Redis can be configured in a master or slave configuration.  This charm
provides a single stand alone implementation of Redis software supporting the
master-slave relationship. Go to the Redis web pages for more information on
[replication](http://redis.io/topics/replication).

# Usage

To deploy this charm first bootstrap your Juju environment and issue the
following command:

    juju deploy redis

Expose the master if you need to contact them for some reason.

    juju expose redis

# Replication

Redis can be set up with master-slave replication in Juju.  This allows the
Redis slave to be an exact copy of master server.  A master can have multiple
slaves.

To set up a master-slave scenario, deploy two services using this charm, one
for the master and one the slave server, then relate the two.

    juju deploy redis redis1
    juju deploy redis redis2
    juju add-relation redis1:master redis2:slave

# Connecting to the charm

The charm provides a `db` relation for services wanting to connect to the Redis
service. When the relation established the following data is passed to the
related units:

- `hostname`: the Redis server host name;
- `port`: the port the Redis server is listening to;
- `password`: the optional authentication password, or an empty string if no
  authentication is required.

# Testing Redis

To test if Redis software is functioning properly, telnet to the Redis private
ip address using port 6379. First you need to retrieve the private address of
the Redis instance, then you can use `juju ssh` to connect to that address,
for instance::

    juju ssh redis/0 telnet `juju run --unit redis/0 "unit-get private-address"` 6379

You can also install the redis-tools package `apt-get install redis-tools`
and connect using the Redis client command:

    redis-cli

From there you can issue [Redis commands](http://redis.io/commands) to test
that Redis is working as intended.

# Development and automated testing.

To create a development environment, obtain a copy of the sources, run
`make sysdeps` to install the required system packages and then `make` to set
up the development virtual environment. At this point, it is possible to run
unit and functional tests, including lint checks, by executing `make check`.

Run `make deploy` to deploy the local copy of the charm for development
purposes on your already bootstrapped environment.

Use `make help` for further information about available make targets.

# Redis Information

- Redis [home page](http://redis.io/)
- Redis [github bug tracker](https://github.com/antirez/redis/issues)
- Redis [documentation](http://redis.io/documentation)
- Redis [mailing list](http://groups.google.com/group/redis-db)
