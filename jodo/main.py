"""Main code for jodo."""
import argparse
import os
from typing import TYPE_CHECKING

from pycloudlib.azure.cloud import Azure
from pycloudlib.cloud import BaseCloud
from pycloudlib.ec2.cloud import EC2
from pycloudlib.gce.cloud import GCE
from pycloudlib.lxd.cloud import LXDContainer, LXDVirtualMachine
from pycloudlib.oci.cloud import OCI
from pycloudlib.openstack.cloud import Openstack

from jodo import db

if TYPE_CHECKING:
    from pycloudlib.instance import BaseInstance

CLOUDS: dict[str, type[BaseCloud]] = {
    "azure": Azure,
    "ec2": EC2,
    "gce": GCE,
    "lxd_container": LXDContainer,
    "lxd_vm": LXDVirtualMachine,
    "oci": OCI,
    "openstack": Openstack,
}


def launch(
    cloud: str,
    name: str,
    image: str,
    instance_type: str,
    userdata: str,
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
    instance: BaseInstance = cloud_class.launch(**kwargs)
    instance.wait()
    db.create_instance(instance, cloud=cloud, name=name)


def list_instances() -> None:
    """List instances."""
    results = db.list_instances()
    table_fields = [x[1:] for x in results]
    table = [("NAME", "CLOUD", "IP", "CREATED"), *table_fields]

    # Calculate the max width of each column then add 2 for more spacing
    widths = [max(len(v) for v in col) + 2 for col in zip(*table, strict=True)]

    # Now print the table
    for row in table:
        items = "".join(f"{row[index]:<{widths[index]}}" for index in range(len(row)))
        print(items)


def ssh(name: str) -> None:
    """SSH to an instance."""
    os.execlp(
        "ssh",
        "ssh",
        f"ubuntu@{db.get_instance(name).ip}",
    )  # noqa: S606 S607


def delete(delete_all: bool, name: str | None) -> None:
    """Delete an instance."""
    instances = []
    if name:
        instances = [db.get_instance(name)]
    if delete_all:
        instances = db.list_instances()
    if not instances:
        print("No instances to delete")
        return
    for instance_info in instances:
        cloud = CLOUDS[instance_info.cloud](tag=instance_info.name)
        instance = cloud.get_instance(instance_info.instance_id)
        instance.delete()
        try:
            db.delete_instance(instance_info.name)
        except ValueError:
            print(f"Could not delete instance '{name}'. Does it exist?")


def main() -> None:
    """Parse arguments and act accordingly."""
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
    parser_delete.add_argument("-a", "--all", action="store_true")
    parser_delete.add_argument("name", nargs="?", default=None)

    args = parser.parse_args()

    if args.command == "launch":
        launch(
            args.cloud,
            args.name,
            args.image,
            args.instance_type,
            args.userdata,
        )
    elif args.command == "list":
        list_instances()
    elif args.command == "ssh":
        ssh(args.name)
    elif args.command == "delete":
        delete(args.all, args.name)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
