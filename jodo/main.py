"""Main code for jodo."""
import argparse
import os
import sys
from typing import Iterator, Optional

from pycloudlib import (
    EC2,
    GCE,
    OCI,
    Azure,
    LXDContainer,
    LXDVirtualMachine,
    Openstack,
    Qemu,
)
from pycloudlib.cloud import BaseCloud
from pycloudlib.instance import BaseInstance
from pycloudlib.util import log_exception_list

from jodo import db

CLOUDS: dict[str, type[BaseCloud]] = {
    "azure": Azure,
    "ec2": EC2,
    "gce": GCE,
    "lxd_container": LXDContainer,
    "lxd_vm": LXDVirtualMachine,
    "oci": OCI,
    "openstack": Openstack,
    "qemu": Qemu,
}


def launch(
    cloud: str,
    name: str,
    image: str,
    instance_type: Optional[str] = None,
    userdata: Optional[str] = None,
) -> None:
    """Launch a new instance."""
    cloud_class = CLOUDS[cloud](tag=name, timestamp_suffix=False)
    try:
        image_id = cloud_class.released_image(image)
    except Exception:
        image_id = image
    kwargs = {"image_id": image_id}
    if instance_type:
        kwargs["instance_type"] = instance_type
    if userdata:
        kwargs["user_data"] = userdata
    db.ensure_not_exists(name=name)
    instance: BaseInstance = cloud_class.launch(**kwargs)
    instance.wait()
    db.create_info(instance, cloud=cloud, name=name)


def list_instances() -> Iterator[str]:
    """List instances."""
    results = db.list_instances()
    table_fields = [x[1:] for x in results]
    table = [("NAME", "CLOUD", "IP", "PORT", "CREATED"), *table_fields]

    # Calculate the max width of each column then add 2 for more spacing
    widths = [max(len(v) for v in col) + 2 for col in zip(*table, strict=True)]

    # Now print the table
    for row in table:
        yield "".join(f"{row[index]:<{widths[index]}}" for index in range(len(row)))


def execute(name: str, command: str, sudo: bool = False) -> str:
    """Execute a command on an instance."""
    result = _get_instance(name).execute(command, use_sudo=sudo)
    output = f"return code: {result.return_code}\nstdout:\n{result.stdout}\n"
    if result.stderr:
        output += f"stderr:\n{result.stderr}"
    return output


def push(name: str, source: str, destination: str) -> None:
    """Push a file to an instance."""
    _get_instance(name).push_file(local_path=source, remote_path=destination)


def pull(name: str, source: str, destination: str) -> None:
    """Pull a file from an instance."""
    _get_instance(name).pull_file(remote_path=source, local_path=destination)


def ssh(name: str) -> None:
    """SSH to an instance."""
    info = db.get_info(name)
    os.execlp(  # noqa: S606
        "ssh",
        "ssh",
        f"ubuntu@{info.ip}",
        "-p",
        info.port,
    )


def delete(name: str) -> None:
    """Delete an instance."""
    instance = _get_instance(name)
    exceptions = instance.delete()
    db.delete_info(name)
    if exceptions:
        print(
            "Deleted instance info, but got problems deleting on cloud. "
            "Ensure instance is actually deleted."
        )
    log_exception_list(exceptions)


def _get_instance(name: str) -> BaseInstance:
    """Get an instance."""
    try:
        instance_info = db.get_info(name)
    except ValueError:
        print(f"Could not find instance '{name}'. Does it exist?")
        sys.exit(1)
    cloud = CLOUDS[instance_info.cloud](tag=instance_info.name)
    return cloud.get_instance(instance_info.instance_id)


def take_action(args: argparse.Namespace) -> None:
    """Take appropriate action based on arguments."""
    match args.command:
        case "launch":
            launch(
                args.cloud,
                args.name,
                args.image,
                args.instance_type,
                args.userdata,
            )
        case "list":
            print("\n".join(list_instances()))
        case "ssh":
            ssh(args.name)
        case "delete":
            delete(args.name)
        case "exec":
            print(execute(args.name, args.exec_command))
        case "push":
            push(args.name, args.source, args.destination)
        case "pull":
            pull(args.name, args.source, args.destination)
        case _:
            raise ValueError("Argparse shouldn't let us get here")  # noqa: TRY003


def parse_args() -> argparse.Namespace:
    """Parse and return arguments."""
    parser = argparse.ArgumentParser(description="One CLI to rule them all")
    subparsers = parser.add_subparsers(help="sub-command", dest="command")

    parser_launch = subparsers.add_parser("launch", help="Launch a new instance")
    parser_launch.add_argument("name")
    parser_launch.add_argument("-c", "--cloud", choices=CLOUDS.keys())
    parser_launch.add_argument("-i", "--image", required=True)
    parser_launch.add_argument("-t", "--instance_type")
    parser_launch.add_argument("-u", "--userdata")

    subparsers.add_parser("list", help="List instances")

    parser_ssh = subparsers.add_parser("ssh", help="SSH to an instance")
    parser_ssh.add_argument("name")

    parser_delete = subparsers.add_parser("delete", help="delete an instance")
    parser_delete.add_argument("name", nargs="?", default=None)

    parser_execute = subparsers.add_parser(
        "exec",
        help="Execute a command on an instance",
    )
    parser_execute.add_argument("-s", "--sudo", action="store_true")
    parser_execute.add_argument("name")
    parser_execute.add_argument("exec_command")

    parser_push = subparsers.add_parser("push", help="Push a file to an instance")
    parser_push.add_argument("name")
    parser_push.add_argument("source")
    parser_push.add_argument("destination")

    parser_pull = subparsers.add_parser("pull", help="Pull a file from an instance")
    parser_pull.add_argument("name")
    parser_pull.add_argument("source")
    parser_pull.add_argument("destination")

    return parser.parse_args()


def main() -> None:
    """Run main function."""
    take_action(parse_args())


if __name__ == "__main__":
    main()
