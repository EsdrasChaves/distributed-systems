# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
import grpc

import services_pb2 as services__pb2


class ServiceStub(object):
  # missing associated documentation comment in .proto file
  pass

  def __init__(self, channel):
    """Constructor.

    Args:
      channel: A grpc.Channel.
    """
    self.create = channel.unary_unary(
        '/Service/create',
        request_serializer=services__pb2.Data.SerializeToString,
        response_deserializer=services__pb2.ServerResponse.FromString,
        )
    self.read = channel.unary_unary(
        '/Service/read',
        request_serializer=services__pb2.Id.SerializeToString,
        response_deserializer=services__pb2.ServerResponse.FromString,
        )
    self.update = channel.unary_unary(
        '/Service/update',
        request_serializer=services__pb2.Data.SerializeToString,
        response_deserializer=services__pb2.ServerResponse.FromString,
        )
    self.delete = channel.unary_unary(
        '/Service/delete',
        request_serializer=services__pb2.Id.SerializeToString,
        response_deserializer=services__pb2.ServerResponse.FromString,
        )


class ServiceServicer(object):
  # missing associated documentation comment in .proto file
  pass

  def create(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def read(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def update(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def delete(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')


def add_ServiceServicer_to_server(servicer, server):
  rpc_method_handlers = {
      'create': grpc.unary_unary_rpc_method_handler(
          servicer.create,
          request_deserializer=services__pb2.Data.FromString,
          response_serializer=services__pb2.ServerResponse.SerializeToString,
      ),
      'read': grpc.unary_unary_rpc_method_handler(
          servicer.read,
          request_deserializer=services__pb2.Id.FromString,
          response_serializer=services__pb2.ServerResponse.SerializeToString,
      ),
      'update': grpc.unary_unary_rpc_method_handler(
          servicer.update,
          request_deserializer=services__pb2.Data.FromString,
          response_serializer=services__pb2.ServerResponse.SerializeToString,
      ),
      'delete': grpc.unary_unary_rpc_method_handler(
          servicer.delete,
          request_deserializer=services__pb2.Id.FromString,
          response_serializer=services__pb2.ServerResponse.SerializeToString,
      ),
  }
  generic_handler = grpc.method_handlers_generic_handler(
      'Service', rpc_method_handlers)
  server.add_generic_rpc_handlers((generic_handler,))