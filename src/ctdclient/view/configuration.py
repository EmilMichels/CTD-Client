import smtplib
import sys
import tkinter as tk
import tkinter.font as tkFont
import webbrowser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import partial
from pathlib import Path
from tkinter import filedialog as fd
from tkinter import ttk

import customtkinter as ctk
from CTkMessagebox import CTkMessagebox

from ctdclient.definitions import RESOURCES_PATH, config
from ctdclient.view.ctkframe import CtkFrame
from ctdclient.view.tabview import TabView
from ctdclient.view.View import ViewMixin


class ConfigurationView(ViewMixin, CtkFrame):
    """ """

    def initialize(self, root):
        super().__init__(master=root)
        self.base_settings = BaseSettings(self)
        self.expert_settings = ExpertSettings(self)
        self.tabs = TabView(
            window=self,
            tabs={
                "basic": self.base_settings,
                "expert": self.expert_settings,
            },
            width=600,
            height=700,
        )
        self.tabs.grid()
        self.tabs.configure(fg_color="transparent")


class BaseSettings(ViewMixin, CtkFrame):
    def initialize(self, root):
        super().__init__(master=root)
        self.values_to_set = self.get_values_to_set()
        for index, (instrument, inner_dict) in enumerate(
            self.values_to_set.items()
        ):
            index *= len(inner_dict) + 2
            ctk.CTkLabel(
                self,
                text=f"{instrument}",
                font=(tkFont.nametofont("TkDefaultFont"), 20),
            ).grid(
                row=index,
                column=0,
                sticky=tk.W,
                padx=self.padx,
                pady=self.pady,
            )
            ttk.Separator(self, orient="horizontal").grid(
                row=index + 1, sticky=tk.E + tk.W
            )
            for inner_index, (name, variable) in enumerate(inner_dict.items()):
                row = index + inner_index + 2
                ctk.CTkLabel(self, text=f"{name.replace('_', ' ')}: ").grid(
                    row=row,
                    column=0,
                    sticky=tk.W,
                    padx=self.padx,
                    pady=self.pady,
                )
                if instrument == "operators":
                    ctk.CTkEntry(self, textvariable=variable).grid(
                        row=row,
                        column=1,
                        sticky=tk.E,
                        padx=self.padx,
                        pady=self.pady,
                    )
                else:
                    if name == "number_of_bottles":
                        variable = tk.IntVar(value=int(variable.get()))
                        inner_dict[name] = variable
                        ctk.CTkEntry(self, textvariable=variable).grid(
                            row=row,
                            column=1,
                            sticky=tk.E,
                            padx=self.padx,
                            pady=self.pady,
                        )
                    else:
                        ctk.CTkLabel(
                            self,
                            textvariable=variable,
                            font=(tkFont.nametofont("TkDefaultFont"), 10),
                        ).grid(
                            row=row,
                            column=1,
                            sticky=tk.E,
                            padx=self.padx,
                            pady=self.pady,
                        )
                        command_with_arguments = partial(
                            self.select_file, instrument, name, variable
                        )
                        ctk.CTkButton(
                            self,
                            text="Browse",
                            command=command_with_arguments,
                            width=28,
                        ).grid(
                            row=row, column=2, padx=self.padx, pady=self.pady
                        )
        ctk.CTkButton(
            self, text="Save", command=self.write_config, width=600
        ).grid(row=row, column=0, columnspan=3, padx=self.padx, pady=self.pady)

    def get_values_to_set(self):
        value_dict = {}
        for instrument in self.configuration.platforms:
            if instrument == "CTD":
                value_dict.update(
                    {
                        instrument: {
                            key: tk.StringVar(value=value)
                            for key, value in self.configuration[
                                instrument.lower()
                            ]["paths"].items()
                        }
                    }
                )
            value_dict.update(
                {
                    "operators": {
                        key: tk.StringVar(value=value)
                        for key, value in self.configuration.operators.items()
                    }
                }
            )
        return value_dict

    def write_config(self, instrument: str = "CTD"):
        self.configuration["operators"] = {
            key: value.get()
            for key, value in self.values_to_set["operators"].items()
        }
        self.configuration[instrument.lower()]["paths"] = {
            key: value.get()
            for key, value in self.values_to_set[instrument].items()
        }
        self.configuration.write(use_internal_values=False)
        self.callbacks["save"]()

    def select_file(self, instrument, name, variable):
        """
        Generic file selection method, that opens a file browsing pop-up.
        """
        if not name.endswith("directory"):
            if name.endswith("psa"):
                file_type = "psa"
            elif name.startswith("batch"):
                file_type = "bat"
            else:
                file_type = name
            path = Path(variable.get())
            filetypes = (
                (f"{file_type} files", f"*.{file_type}"),
                ("All files", "*.*"),
            )

            file = fd.askopenfilename(
                title=f"Path to {name}",
                initialdir=path.parent,
                initialfile=path.name,
                filetypes=filetypes,
            )
        else:
            file = fd.askdirectory(
                title=f"{name}",
                initialdir=variable.get(),
            )
        if file:
            variable.set(file)
            self.configuration[instrument.lower()]["paths"][name] = file
            self.configuration.write(use_internal_values=False)


class ExpertSettings(ctk.CTkScrollableFrame):
    def initialize(self, root):
        super().__init__(master=root)
        self.configuration = config
        self.configure(
            height=500,
            width=600,
            fg_color="gray16",
        )
        self.padx = 5
        self.pady = 5
        self.values = self.get_values_to_set()
        self.platform_options = ["CTD"]
        top_entry_length = len(self.values["base"])
        for index, (setting, inner_dict) in enumerate(self.values.items()):
            index *= top_entry_length + len(self.platform_options) + 4
            ctk.CTkLabel(
                self,
                text=f"{setting}",
                font=(tkFont.nametofont("TkDefaultFont"), 20),
            ).grid(
                row=index,
                column=0,
                sticky=tk.W,
                padx=self.padx,
                pady=self.pady,
            )
            ttk.Separator(self, orient="horizontal").grid(
                row=index + 1, sticky=tk.E + tk.W
            )
            for inner_index, (name, (variable, param_type)) in enumerate(
                inner_dict.items()
            ):
                row = index + inner_index + 2
                if param_type is bool:
                    variable = tk.BooleanVar(value=variable.get())
                    inner_dict[name] = (variable, param_type)
                    ctk.CTkSwitch(
                        self,
                        variable=variable,
                        text="",
                    ).grid(
                        row=row,
                        column=1,
                        sticky=tk.E,
                        padx=self.padx,
                        pady=self.pady,
                    )
                elif name.endswith(("exe", "dir", "print", "exes")):
                    ctk.CTkLabel(
                        self,
                        textvariable=variable,
                        font=(tkFont.nametofont("TkDefaultFont"), 10),
                    ).grid(
                        row=row,
                        column=1,
                        sticky=tk.E,
                        padx=self.padx,
                        pady=self.pady,
                    )
                    command_with_arguments = partial(
                        self.select_file, name, variable
                    )
                    ctk.CTkButton(
                        self,
                        text="Browse",
                        command=command_with_arguments,
                        width=28,
                        font=(tkFont.nametofont("TkDefaultFont"), 10),
                    ).grid(row=row, column=2, padx=self.padx, pady=self.pady)
                elif name.endswith("platforms"):
                    continue
                else:
                    ctk.CTkEntry(self, textvariable=variable).grid(
                        row=row,
                        column=1,
                        sticky=tk.E,
                        padx=self.padx,
                        pady=self.pady,
                    )
                ctk.CTkLabel(self, text=f"{name.replace('_', ' ')}: ").grid(
                    row=row,
                    column=0,
                    sticky=tk.W,
                    padx=self.padx,
                    pady=self.pady,
                )
        ctk.CTkButton(
            self, text="Save", command=self.write_config, width=600
        ).grid(
            row=row + 1, column=0, columnspan=3, padx=self.padx, pady=self.pady
        )

    def get_values_to_set(self):
        value_dict = {
            "base": {"platforms": self.configuration["base"]["platforms"]}
        }

        value_dict["base"].update(
            {
                key: (tk.StringVar(value=value), type(value))
                for key, value in self.configuration["base"].items()
                if key != "platforms"
            }
        )
        value_dict.update(
            {
                "dship parameters": {
                    key: (tk.StringVar(value=value), type(value))
                    for key, value in self.configuration["dship"][
                        "identifier"
                    ].items()
                }
            }
        )
        value_dict.update(
            {
                "email config": {
                    key: (tk.StringVar(value=value), type(value))
                    for key, value in self.configuration["email"].items()
                }
            }
        )
        return value_dict

    def write_config(self):
        new_base = {}
        for key, value in self.values["base"].items():
            if key != "platforms":
                new_base[key] = value[0].get()
            else:
                new_base[key] = value

        self.configuration["base"] = new_base
        self.configuration["dship"]["identifier"] = {
            key: value[0].get()
            for key, value in self.values["dship parameters"].items()
        }
        self.configuration["email"] = {
            key: value[0].get()
            for key, value in self.values["email config"].items()
        }
        self.configuration.write(use_internal_values=False)
        CTkMessagebox(
            title="Info",
            message="You need to restart the application for these settings to have an effect.",
            option_1="Ok",
        )

    def select_file(self, name, variable):
        """
        Generic file selection method, that opens a file browsing pop-up.
        """
        path = Path(variable.get())
        if name.endswith("exe"):
            file_type = "exe"
            filetypes = (
                (f"{file_type} files", f"*.{file_type}"),
                ("All files", "*.*"),
            )

            file = fd.askopenfilename(
                title=f"Path to {name}",
                initialdir=path.parent,
                initialfile=path.name,
                filetypes=filetypes,
            )
        else:
            file = fd.askdirectory(
                title=f"Path to {name}",
                initialdir=path.parent,
            )
        variable.set(file)


class AboutView(CtkFrame):
    def initialize(self, root):
        super().__init__(master=root)
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text="This is the CTD-Client developed at the IOW for the DAM.\nIt is meant to help in and streamline the CTD-Data-Acquisition.\n\nThe documentation can be found here:",
        ).grid(row=0, column=0, padx=self.padx, pady=self.pady)
        if getattr(sys, "frozen", False):
            docs = f"file://{RESOURCES_PATH.absolute()}/htmls/usage.html"
            text = "Documentation"
        else:
            docs = "https://ctd-software.pages.io-warnemuende.de/CTD-Client/usage.html"
            text = "Online documentation"
        ctk.CTkButton(
            self,
            text=text,
            command=lambda: webbrowser.open_new_tab(docs),
        ).grid(row=1, column=0, padx=self.padx, pady=self.pady)
        ctk.CTkLabel(
            self,
            text="Developed and maintained by Emil Michels, IOW.\nFeel free to contact me anytime.\n",
        ).grid(row=3, column=0, padx=self.padx, pady=self.pady)
        contact_links = ctk.CTkFrame(self, fg_color="transparent")
        contact_links.grid(row=4, column=0, padx=self.padx, pady=self.pady)

        # email form
        ctk.CTkLabel(
            contact_links,
            text="You can send me an email using the following form (and the local email server):",
        ).grid(row=2)
        email_form = ctk.CTkFrame(
            contact_links,
            fg_color="transparent",
            border_width=1,
            border_color="gray10",
        )
        email_form.grid(row=3, column=0, padx=self.padx, pady=self.pady)

        label_name = ctk.CTkLabel(email_form, text="Name:")
        label_name.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        self.entry_name = ctk.CTkEntry(email_form, width=300)
        self.entry_name.grid(row=0, column=1, padx=self.padx, pady=self.pady)

        label_email = ctk.CTkLabel(email_form, text="Email:")
        label_email.grid(row=1, column=0, padx=self.padx, pady=self.pady)
        self.entry_email = ctk.CTkEntry(email_form, width=300)
        self.entry_email.grid(row=1, column=1, padx=self.padx, pady=self.pady)

        label_subject = ctk.CTkLabel(email_form, text="Subject:")
        label_subject.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        self.entry_subject = ctk.CTkEntry(email_form, width=300)
        self.entry_subject.grid(
            row=2, column=1, padx=self.padx, pady=self.pady
        )

        label_message = ctk.CTkLabel(email_form, text="Message:")
        label_message.grid(row=3, column=0, padx=self.padx, pady=self.pady)
        self.text_message = ctk.CTkTextbox(email_form, width=300, height=150)
        self.text_message.grid(row=3, column=1, padx=self.padx, pady=self.pady)

        button_send = ctk.CTkButton(
            email_form, text="Send", command=self.send_email
        )
        button_send.grid(row=4, column=1, columnspan=2, pady=self.pady * 4)

    def send_email(self):
        """Send the email using the local SMTP server."""
        try:
            name = self.entry_name.get()
            email = self.entry_email.get()
            subject = self.entry_subject.get()
            message = self.text_message.get("1.0", "end-1c")

            msg = MIMEMultipart()
            msg["From"] = config.email_config["smtp_email"]
            msg["To"] = "emil.michels@io-warnemuende.de"
            msg["Subject"] = subject
            body = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(
                config.email_config["smtp_server"],
                config.email_config["smtp_port"],
            ) as server:
                server.send_message(msg)

            CTkMessagebox(
                title="Success",
                message="Email sent successfully!",
                option_1="Ok",
            )
        except Exception as e:
            CTkMessagebox(
                title="Error",
                message=f"Failed to send email: {e}",
                option_1="Ok",
            )
