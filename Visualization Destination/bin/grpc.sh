#!/bin/bash

cd protos
python -m grpc_tools.protoc -I../../../../Pipeline/Core/protos:../../../Interface/proto/:.  --python_out=. --grpc_python_out=. visualization.proto
mv *.py ../src