package com.arturgpt.skufaddon.client.render;

import com.arturgpt.skufaddon.common.machine.singleblock.tilt.SkufTiltMachine;

import net.minecraft.client.Camera;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.block.model.BakedQuad;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.client.resources.model.BakedModel;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.client.event.RenderLevelStageEvent;
import net.minecraftforge.client.model.data.ModelData;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.level.LevelEvent;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;

import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Set;

/**
 * Client-side renderer that makes Tilt machines glow red once they have been stuck in the
 * "Ваще похуй" (peak tilt) mode long enough to overheat. The machine's own model quads are
 * re-rendered as a translucent, emissive, red-tinted decal layered on its surface.
 *
 * <p>
 * Machines register/unregister themselves from their client tick; the geometry is drawn once
 * per frame during {@link RenderLevelStageEvent.Stage#AFTER_TRANSLUCENT_BLOCKS}. Client ticks and
 * world rendering both run on the main client thread, so a plain identity set is enough.
 */
public final class SkufOverheatRenderer {

    private static final Set<SkufTiltMachine> ACTIVE = Collections.newSetFromMap(new IdentityHashMap<>());

    private static final Direction[] DIRECTIONS_AND_NULL = {
            Direction.DOWN, Direction.UP, Direction.NORTH, Direction.SOUTH, Direction.WEST, Direction.EAST, null
    };

    /** Pulse speed (radians per game tick). */
    private static final float PULSE_SPEED = 0.25f;
    /** Maximum blended alpha of the glow at full heat. */
    private static final float MAX_ALPHA = 0.8f;

    private static final RandomSource QUAD_RANDOM = RandomSource.create();

    /** Per-vertex brightness multipliers (no ambient occlusion darkening) and full-bright lightmap. */
    private static final float[] FULL_BRIGHTNESS = { 1.0f, 1.0f, 1.0f, 1.0f };
    private static final int[] EMISSIVE_LIGHT = {
            LightTexture.FULL_BRIGHT, LightTexture.FULL_BRIGHT, LightTexture.FULL_BRIGHT, LightTexture.FULL_BRIGHT
    };

    private SkufOverheatRenderer() {}

    public static void init() {
        MinecraftForge.EVENT_BUS.addListener(SkufOverheatRenderer::onRenderLevelStage);
        MinecraftForge.EVENT_BUS.addListener(SkufOverheatRenderer::onLevelUnload);
    }

    public static void setActive(SkufTiltMachine machine, boolean active) {
        if (active) {
            ACTIVE.add(machine);
        } else {
            ACTIVE.remove(machine);
        }
    }

    private static void onLevelUnload(LevelEvent.Unload event) {
        if (event.getLevel().isClientSide()) {
            ACTIVE.clear();
        }
    }

    private static void onRenderLevelStage(RenderLevelStageEvent event) {
        if (event.getStage() != RenderLevelStageEvent.Stage.AFTER_TRANSLUCENT_BLOCKS || ACTIVE.isEmpty()) {
            return;
        }

        Minecraft mc = Minecraft.getInstance();
        ClientLevel level = mc.level;
        if (level == null) {
            return;
        }

        Camera camera = event.getCamera();
        Vec3 cam = camera.getPosition();
        PoseStack pose = event.getPoseStack();
        MultiBufferSource.BufferSource buffers = mc.renderBuffers().bufferSource();
        VertexConsumer consumer = buffers.getBuffer(SkufOverheatRenderType.OVERHEAT_GLOW);

        float time = (float) level.getGameTime() + event.getPartialTick();
        float pulse = 0.7f + 0.3f * Mth.sin(time * PULSE_SPEED);

        for (SkufTiltMachine machine : ACTIVE) {
            if (machine.getLevel() != level) {
                continue;
            }
            float heat = machine.getClientGlowIntensity();
            if (heat <= 0.01f) {
                continue;
            }

            float alpha = Mth.clamp(heat * pulse, 0.0f, 1.0f) * MAX_ALPHA;
            if (alpha <= 0.0f) {
                continue;
            }
            // Tint shifts from orange (warming up) to a deep saturated red (fully overheated).
            float red = 1.0f;
            float green = 0.05f + 0.35f * (1.0f - heat);
            float blue = 0.03f;

            BlockPos pos = machine.getPos();
            renderMachineGlow(machine, level, pos, consumer, pose, cam, red, green, blue, alpha);
        }

        buffers.endBatch(SkufOverheatRenderType.OVERHEAT_GLOW);
    }

    private static void renderMachineGlow(SkufTiltMachine machine, ClientLevel level, BlockPos pos,
                                          VertexConsumer consumer, PoseStack pose, Vec3 cam,
                                          float red, float green, float blue, float alpha) {
        BlockState state = machine.getBlockState();
        BakedModel model = Minecraft.getInstance().getBlockRenderer().getBlockModel(state);
        ModelData modelData = model.getModelData(level, pos, state, ModelData.EMPTY);
        long seed = state.getSeed(pos);

        pose.pushPose();
        pose.translate(pos.getX() - cam.x, pos.getY() - cam.y, pos.getZ() - cam.z);
        PoseStack.Pose entry = pose.last();

        for (Direction direction : DIRECTIONS_AND_NULL) {
            QUAD_RANDOM.setSeed(seed);
            List<BakedQuad> quads = model.getQuads(state, direction, QUAD_RANDOM, modelData, null);
            for (BakedQuad quad : quads) {
                consumer.putBulkData(entry, quad, FULL_BRIGHTNESS, red, green, blue, alpha,
                        EMISSIVE_LIGHT, OverlayTexture.NO_OVERLAY, true);
            }
        }

        pose.popPose();
    }
}
