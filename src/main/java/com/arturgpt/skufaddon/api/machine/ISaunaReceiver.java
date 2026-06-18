package com.arturgpt.skufaddon.api.machine;

import org.jetbrains.annotations.Nullable;

/**
 * Implemented by a machine that can receive a sauna environment from an {@link ISaunaProvider}.
 */
public interface ISaunaReceiver {

    /**
     * @return the sauna this machine is currently bound to, or {@code null} if none
     */
    @Nullable
    ISaunaProvider getSauna();

    /**
     * Binds this machine to the given sauna (or {@code null} to unbind).
     *
     * @param provider the sauna to assign to this machine
     */
    void setSauna(@Nullable ISaunaProvider provider);
}
